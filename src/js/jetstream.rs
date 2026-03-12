use std::{ops::Deref, sync::Arc};

use async_nats::{Subject, client::traits::Publisher, connection::State};
use pyo3::{
    Bound, PyAny, Python, pyclass, pymethods,
    types::{PyBytes, PyBytesMethods, PyDict},
};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::{
        kv::{KVConfig, KeyValue},
        stream::StreamConfig,
    },
    utils::{headers::NatsrpyHeadermapExt, natsrpy_future},
};

#[pyclass]
pub struct JetStream {
    ctx: Arc<RwLock<async_nats::jetstream::Context>>,
}

impl JetStream {
    #[must_use]
    pub fn new(ctx: async_nats::jetstream::Context) -> Self {
        Self {
            ctx: Arc::new(RwLock::new(ctx)),
        }
    }
}

#[pymethods]
impl JetStream {
    #[pyo3(signature = (
        subject,
        payload,
        *,
        headers=None,
        reply=None,
        err_on_disconnect = false
    ))]
    pub fn publish<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        payload: &Bound<PyBytes>,
        headers: Option<Bound<PyDict>>,
        reply: Option<String>,
        err_on_disconnect: bool,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        let data = bytes::Bytes::from(payload.as_bytes().to_vec());
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        natsrpy_future(py, async move {
            if err_on_disconnect
                && ctx.read().await.client().connection_state() == State::Disconnected
            {
                return Err(NatsrpyError::Disconnected);
            }
            ctx.read()
                .await
                .publish_message(async_nats::message::OutboundMessage {
                    subject: Subject::from(subject),
                    payload: data,
                    headers: headermap,
                    reply: reply.map(Subject::from),
                })
                .await?;
            Ok(())
        })
    }

    pub fn create_kv<'py>(
        &self,
        py: Python<'py>,
        config: &Bound<'py, KVConfig>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        let config = config.borrow().deref().clone().try_into()?;

        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(KeyValue::new(js.create_key_value(config).await?))
        })
    }

    pub fn get_kv<'py>(&self, py: Python<'py>, bucket: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(KeyValue::new(js.get_key_value(bucket).await?))
        })
    }

    pub fn update_kv<'py>(
        &self,
        py: Python<'py>,
        config: &Bound<'py, KVConfig>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        let config = config.borrow().deref().clone().try_into()?;
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(KeyValue::new(js.update_key_value(config).await?))
        })
    }

    pub fn delete_kv<'py>(
        &self,
        py: Python<'py>,
        bucket: String,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(js.delete_key_value(bucket).await?.success)
        })
    }

    pub fn create_stream<'py>(
        &self,
        py: Python<'py>,
        config: StreamConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(super::stream::Stream::new(
                js.create_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                    .await?,
            ))
        })
    }
}
