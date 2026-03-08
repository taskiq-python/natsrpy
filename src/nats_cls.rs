use async_nats::{Subject, client::traits::Publisher, message::OutboundMessage};
use pyo3::{
    Bound, PyAny, PyResult, Python, pyclass, pymethods,
    types::{PyBytes, PyBytesMethods, PyDict},
};
use std::{sync::Arc, time::Duration};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::NatsrpyError,
    subscription::Subscription,
    utils::{headers::NatsrpyHeadermapExt, natsrpy_future},
};

#[pyclass(name = "Nats")]
pub struct NatsCls {
    nats_session: Arc<tokio::sync::RwLock<Option<async_nats::Client>>>,
    addr: Vec<String>,
    user_and_pass: Option<(String, String)>,
    nkey: Option<String>,
    token: Option<String>,
    custom_inbox_prefix: Option<String>,
    read_buffer_capacity: u16,
    sender_capacity: usize,
    max_reconnects: Option<usize>,
    connection_timeout: f32,
    request_timeout: f32,
}

#[pymethods]
impl NatsCls {
    #[new]
    #[pyo3(signature = (
        /,
        addrs=vec![String::from("nats://localhost:4222")],
        user_and_pass=None,
        nkey=None,
        token=None,
        custom_inbox_prefix=None,
        read_buffer_capacity=65535,
        sender_capacity=128,
        max_reconnects=None,
        connection_timeout=5.0,
        request_timeout=10.0,
    ))]
    fn __new__(
        addrs: Vec<String>,
        user_and_pass: Option<(String, String)>,
        nkey: Option<String>,
        token: Option<String>,
        custom_inbox_prefix: Option<String>,
        read_buffer_capacity: u16,
        sender_capacity: usize,
        max_reconnects: Option<usize>,
        connection_timeout: f32,
        request_timeout: f32,
    ) -> PyResult<Self> {
        Ok(Self {
            nats_session: Arc::new(RwLock::new(None)),
            user_and_pass,
            nkey,
            token,
            custom_inbox_prefix,
            read_buffer_capacity,
            sender_capacity,
            max_reconnects,
            connection_timeout,
            request_timeout,
            addr: addrs,
        })
    }
    pub fn startup<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        let mut conn_opts = async_nats::ConnectOptions::new();
        if let Some((username, passwd)) = &self.user_and_pass {
            conn_opts = conn_opts.user_and_password(username.to_string(), passwd.to_string());
        }
        if let Some(nkey) = &self.nkey {
            conn_opts = conn_opts.nkey(nkey.to_string());
        }
        conn_opts = conn_opts
            .max_reconnects(self.max_reconnects)
            .connection_timeout(std::time::Duration::from_secs_f32(self.connection_timeout))
            .request_timeout(Some(std::time::Duration::from_secs_f32(
                self.request_timeout,
            )))
            .read_buffer_capacity(self.read_buffer_capacity)
            .client_capacity(self.sender_capacity);

        if let Some(token) = &self.token {
            conn_opts = conn_opts.token(token.to_string());
        }
        if let Some(custom_inbox_prefix) = &self.custom_inbox_prefix {
            conn_opts = conn_opts.custom_inbox_prefix(custom_inbox_prefix);
        }

        let session = self.nats_session.clone();
        let address = self.addr.clone();
        let startup_future = async move {
            if session.read().await.is_some() {
                return Err(NatsrpyError::SessionError(
                    "NATS session already exists".to_string(),
                ));
            }
            let mut sesion_guard = session.write().await;
            *sesion_guard = Some(conn_opts.connect(address).await?);
            Ok(())
        };
        let timeout = Duration::from_secs_f32(self.connection_timeout);
        return Ok(natsrpy_future(py, async move {
            tokio::time::timeout(timeout, startup_future).await?
        })?);
    }

    #[pyo3(signature = (subject, payload, *, headers=None, reply=None, err_on_disconnect = false))]
    pub fn publish<'a>(
        &self,
        py: Python<'a>,
        subject: String,
        payload: Bound<PyBytes>,
        headers: Option<Bound<PyDict>>,
        reply: Option<String>,
        err_on_disconnect: bool,
    ) -> PyResult<Bound<'a, PyAny>> {
        let session = self.nats_session.clone();
        let data = bytes::Bytes::copy_from_slice(payload.as_bytes());
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        Ok(natsrpy_future(py, async move {
            let write_guard = session.read().await;
            let Some(session) = write_guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            if err_on_disconnect
                && session.connection_state() == async_nats::connection::State::Disconnected
            {
                return Err(NatsrpyError::Disconnected);
            }
            session
                .publish_message(OutboundMessage {
                    subject: Subject::from(subject),
                    payload: data,
                    headers: headermap,
                    reply: reply.map(Subject::from),
                })
                .await?;
            Ok(())
        })?)
    }

    #[pyo3(signature = (subject, payload, *, headers=None, inbox = None, timeout=None))]
    pub fn request<'a>(
        &self,
        py: Python<'a>,
        subject: String,
        payload: Option<Bound<PyBytes>>,
        headers: Option<Bound<PyDict>>,
        inbox: Option<String>,
        timeout: Option<f32>,
    ) -> PyResult<Bound<'a, PyAny>> {
        let session = self.nats_session.clone();
        let data = payload.map(|inner| bytes::Bytes::from(inner.as_bytes().to_vec()));
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        Ok(natsrpy_future(py, async move {
            let write_guard = session.read().await;
            let Some(session) = write_guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            let request = async_nats::Request {
                payload: data,
                headers: headermap,
                inbox: inbox,
                timeout: timeout.map(|t| Some(std::time::Duration::from_secs_f32(t))),
            };
            session.send_request(subject, request).await?;
            Ok(())
        })?)
    }

    pub fn drain<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        log::debug!("Draining NATS session");
        let session = self.nats_session.clone();
        Ok(natsrpy_future(py, async move {
            let write_guard = session.write().await;
            let Some(session) = write_guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            session.drain().await?;
            Ok(())
        })?)
    }

    pub fn subscribe<'a>(&self, py: Python<'a>, subject: String) -> PyResult<Bound<'a, PyAny>> {
        log::debug!("Subscribing to '{}'", subject);
        let session = self.nats_session.clone();
        Ok(natsrpy_future(py, async move {
            let guard = session.read().await;
            let Some(session) = guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            Ok(Subscription::new(session.subscribe(subject).await?))
        })?)
    }

    #[pyo3(signature = (
        *,
        domain=None,
        api_prefix=None,
        timeout=None,
        ack_timeout=None,
        concurrency_limit = None,
        max_ack_inflight=None,
        backpressure_on_inflight=None,
    ))]
    pub fn jetstream<'a>(
        &self,
        py: Python<'a>,
        domain: Option<String>,
        api_prefix: Option<String>,
        timeout: Option<f32>,
        ack_timeout: Option<f32>,
        concurrency_limit: Option<usize>,
        max_ack_inflight: Option<usize>,
        backpressure_on_inflight: Option<bool>,
    ) -> PyResult<Bound<'a, PyAny>> {
        log::debug!("Creating JetStream context");
        let session = self.nats_session.clone();
        Ok(natsrpy_future(py, async move {
            let guard = session.read().await;
            let Some(session) = guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            let mut builder =
                async_nats::jetstream::ContextBuilder::new().concurrency_limit(concurrency_limit);
            if let Some(timeout) = ack_timeout {
                builder = builder.ack_timeout(Duration::from_secs_f32(timeout));
            }
            if let Some(timeout) = timeout {
                builder = builder.timeout(Duration::from_secs_f32(timeout));
            }
            if let Some(max_ack_inflight) = max_ack_inflight {
                builder = builder.max_ack_inflight(max_ack_inflight);
            }
            if let Some(backpressure_on_inflight) = backpressure_on_inflight {
                builder = builder.backpressure_on_inflight(backpressure_on_inflight);
            }
            if domain.is_some() && api_prefix.is_some() {
                return Err(NatsrpyError::InvalidArgument(String::from(
                    "Either domain or api_prefix should be specified, not both.",
                )));
            }
            let js = if let Some(api_prefix) = api_prefix {
                builder.api_prefix(api_prefix).build(session.clone())
            } else if let Some(domain) = domain {
                builder.domain(domain).build(session.clone())
            } else {
                builder.build(session.clone())
            };
            Ok(crate::jetstream::JetStream::new(js))
        })?)
    }

    pub fn close<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        log::debug!("Closing nats session");
        let session = self.nats_session.clone();
        Ok(natsrpy_future(py, async move {
            let mut write_guard = session.write().await;
            let Some(session) = write_guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            session.drain().await?;
            *write_guard = None;
            Ok(())
        })?)
    }

    pub fn flush<'a>(&self, py: Python<'a>) -> PyResult<Bound<'a, PyAny>> {
        log::debug!("Flushing streams");
        let session = self.nats_session.clone();
        Ok(natsrpy_future(py, async move {
            let write_guard = session.write().await;
            let Some(session) = write_guard.as_ref() else {
                return Err(NatsrpyError::NotInitialized);
            };
            session.flush().await?;
            Ok(())
        })?)
    }
}

impl Drop for NatsCls {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            let mut write_guard = self.nats_session.write().await;
            if let Some(session) = write_guard.as_ref() {
                log::warn!(
                    "NATS session was not closed before dropping. Draining session in drop. Please call `.close()` function before dropping the session to avoid this warning."
                );
                session.drain().await.ok();
            }
            *write_guard = None;
        });
    }
}
