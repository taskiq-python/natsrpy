use async_nats::{Subject, client::traits::Publisher, message::OutboundMessage};
use pyo3::{Bound, IntoPyObjectExt, Py, PyAny, Python, types::PyDict};
use std::sync::{Arc, RwLock};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    subscriptions::{callback::CallbackSubscription, iterator::IteratorSubscription},
    utils::{
        futures::natsrpy_future_with_timeout,
        headers::NatsrpyHeadermapExt,
        natsrpy_future,
        py_types::{SendableValue, TimeValue},
    },
};

#[pyo3::pyclass(name = "Nats")]
pub struct NatsCls {
    nats_session: Arc<RwLock<Option<async_nats::Client>>>,
    addr: Vec<String>,
    user_and_pass: Option<(String, String)>,
    nkey: Option<String>,
    token: Option<String>,
    custom_inbox_prefix: Option<String>,
    read_buffer_capacity: u16,
    sender_capacity: usize,
    max_reconnects: Option<usize>,
    connection_timeout: TimeValue,
    request_timeout: Option<TimeValue>,
}

/// Helper to read the client from the `RwLock`. Returns a clone of the Client if present.
fn get_client(session: &RwLock<Option<async_nats::Client>>) -> NatsrpyResult<async_nats::Client> {
    session
        .read()
        .map_err(|_| NatsrpyError::SessionError("Lock poisoned".to_string()))?
        .clone()
        .ok_or(NatsrpyError::NotInitialized)
}

#[pyo3::pymethods]
impl NatsCls {
    #[new]
    #[pyo3(signature = (
        /,
        addrs=None,
        user_and_pass=None,
        nkey=None,
        token=None,
        custom_inbox_prefix=None,
        read_buffer_capacity=65535,
        sender_capacity=128,
        max_reconnects=None,
        connection_timeout=TimeValue::FloatSecs(5.0),
        request_timeout=TimeValue::FloatSecs(10.0),
    ))]
    fn __new__(
        addrs: Option<Vec<String>>,
        user_and_pass: Option<(String, String)>,
        nkey: Option<String>,
        token: Option<String>,
        custom_inbox_prefix: Option<String>,
        read_buffer_capacity: u16,
        sender_capacity: usize,
        max_reconnects: Option<usize>,
        connection_timeout: TimeValue,
        request_timeout: Option<TimeValue>,
    ) -> Self {
        Self {
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
            addr: addrs.unwrap_or_else(|| vec![String::from("nats://localhost:4222")]),
        }
    }

    pub fn startup<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let mut conn_opts = async_nats::ConnectOptions::new();
        if let Some((username, passwd)) = &self.user_and_pass {
            conn_opts = conn_opts.user_and_password(username.clone(), passwd.clone());
        }
        if let Some(nkey) = &self.nkey {
            conn_opts = conn_opts.nkey(nkey.clone());
        }
        conn_opts = conn_opts
            .max_reconnects(self.max_reconnects)
            .connection_timeout(self.connection_timeout.into())
            .request_timeout(self.request_timeout.map(Into::into))
            .read_buffer_capacity(self.read_buffer_capacity)
            .client_capacity(self.sender_capacity);

        if let Some(token) = &self.token {
            conn_opts = conn_opts.token(token.clone());
        }
        if let Some(custom_inbox_prefix) = &self.custom_inbox_prefix {
            conn_opts = conn_opts.custom_inbox_prefix(custom_inbox_prefix);
        }

        let session = self.nats_session.clone();
        let address = self.addr.clone();
        let timeout = self.connection_timeout;
        natsrpy_future_with_timeout(py, Some(timeout), async move {
            {
                let guard = session
                    .read()
                    .map_err(|_| NatsrpyError::SessionError("Lock poisoned".to_string()))?;
                if guard.is_some() {
                    return Err(NatsrpyError::SessionError(
                        "NATS session already exists".to_string(),
                    ));
                }
            }
            let client = conn_opts.connect(address).await?;
            {
                let mut guard = session
                    .write()
                    .map_err(|_| NatsrpyError::SessionError("Lock poisoned".to_string()))?;
                *guard = Some(client);
            }
            Ok(())
        })
    }

    #[pyo3(signature = (subject, payload, *, headers=None, reply=None, err_on_disconnect = false))]
    pub fn publish<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        payload: SendableValue,
        headers: Option<Bound<PyDict>>,
        reply: Option<String>,
        err_on_disconnect: bool,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = get_client(&self.nats_session)?;
        let data = bytes::Bytes::from(payload);
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        log::debug!(
            "Nats.publish is called with a message to subject '{}' with payload of size {} bytes",
            subject,
            data.len()
        );
        natsrpy_future(py, async move {
            if err_on_disconnect
                && client.connection_state() == async_nats::connection::State::Disconnected
            {
                return Err(NatsrpyError::Disconnected);
            }
            client
                .publish_message(OutboundMessage {
                    subject: Subject::from(subject),
                    payload: data,
                    headers: headermap,
                    reply: reply.map(Subject::from),
                })
                .await?;
            Ok(())
        })
    }

    #[pyo3(signature = (subject, payload, *, headers=None, inbox = None, timeout=None))]
    pub fn request<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        payload: Option<SendableValue>,
        headers: Option<Bound<PyDict>>,
        inbox: Option<String>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = get_client(&self.nats_session)?;
        let data = payload.map(bytes::Bytes::from);
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        log::debug!(
            "Nats.request is called with a message to subject '{}' with payload of size {} bytes",
            subject,
            data.as_ref().map_or(0, bytes::Bytes::len)
        );
        natsrpy_future(py, async move {
            let request = async_nats::Request {
                payload: data,
                headers: headermap,
                inbox,
                timeout: timeout.map(Into::into).map(Some),
            };
            crate::message::Message::try_from(client.send_request(subject, request).await?)
        })
    }

    pub fn drain<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        log::debug!("Draining NATS session");
        let client = get_client(&self.nats_session)?;
        natsrpy_future(py, async move {
            client.drain().await?;
            Ok(())
        })
    }

    #[pyo3(signature=(subject, callback=None, queue=None))]
    pub fn subscribe<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        callback: Option<Py<PyAny>>,
        queue: Option<String>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        log::debug!("Subscribing to '{subject}'");
        let client = get_client(&self.nats_session)?;
        natsrpy_future(py, async move {
            let subscriber = if let Some(queue) = queue {
                client.queue_subscribe(subject, queue).await?
            } else {
                client.subscribe(subject).await?
            };
            if let Some(cb) = callback {
                let sub = CallbackSubscription::new(subscriber, cb)?;
                Ok(Python::attach(|gil| sub.into_py_any(gil))?)
            } else {
                let sub = IteratorSubscription::new(subscriber);
                Ok(Python::attach(|gil| sub.into_py_any(gil))?)
            }
        })
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
    pub fn jetstream<'py>(
        &self,
        py: Python<'py>,
        domain: Option<String>,
        api_prefix: Option<String>,
        timeout: Option<TimeValue>,
        ack_timeout: Option<TimeValue>,
        concurrency_limit: Option<usize>,
        max_ack_inflight: Option<usize>,
        backpressure_on_inflight: Option<bool>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        log::debug!("Creating JetStream context");
        if domain.is_some() && api_prefix.is_some() {
            return Err(NatsrpyError::InvalidArgument(String::from(
                "Either domain or api_prefix should be specified, not both.",
            )));
        }
        let client = get_client(&self.nats_session)?;
        natsrpy_future(py, async move {
            let mut builder =
                async_nats::jetstream::ContextBuilder::new().concurrency_limit(concurrency_limit);
            if let Some(timeout) = ack_timeout {
                builder = builder.ack_timeout(timeout.into());
            }
            if let Some(timeout) = timeout {
                builder = builder.timeout(timeout.into());
            }
            if let Some(max_ack_inflight) = max_ack_inflight {
                builder = builder.max_ack_inflight(max_ack_inflight);
            }
            if let Some(backpressure_on_inflight) = backpressure_on_inflight {
                builder = builder.backpressure_on_inflight(backpressure_on_inflight);
            }
            let js = if let Some(api_prefix) = api_prefix {
                builder.api_prefix(api_prefix).build(client)
            } else if let Some(domain) = domain {
                builder.domain(domain).build(client)
            } else {
                builder.build(client)
            };
            Ok(crate::js::jetstream::JetStream::new(js))
        })
    }

    pub fn shutdown<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        log::debug!("Closing nats session");
        let session = self.nats_session.clone();
        let client = get_client(&session)?;
        // Set session to None immediately so no new operations can start.
        {
            let mut guard = session
                .write()
                .map_err(|_| NatsrpyError::SessionError("Lock poisoned".to_string()))?;
            *guard = None;
        }
        natsrpy_future(py, async move {
            client.drain().await?;
            Ok(())
        })
    }

    pub fn flush<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        log::debug!("Flushing streams");
        let client = get_client(&self.nats_session)?;
        natsrpy_future(py, async move {
            client.flush().await?;
            Ok(())
        })
    }
}

impl Drop for NatsCls {
    fn drop(&mut self) {
        let client = {
            let Ok(mut guard) = self.nats_session.write() else {
                return;
            };
            guard.take()
        };
        if let Some(client) = client {
            log::warn!(
                "NATS session was not closed before dropping. Draining session in drop. Please call `.shutdown()` function before dropping the session to avoid this warning."
            );
            pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
                client.drain().await.ok();
            });
        }
    }
}
