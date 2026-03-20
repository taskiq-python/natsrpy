use std::sync::Arc;

use async_nats::{Subject, client::traits::Publisher, connection::State};
use pyo3::{
    Bound, PyAny, Python,
    types::{PyBytes, PyBytesMethods, PyDict},
};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::managers::{kv::KVManager, streams::StreamsManager},
    utils::{headers::NatsrpyHeadermapExt, natsrpy_future},
};

#[pyo3::pyclass]
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

#[pyo3::pymethods]
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

    #[getter]
    #[must_use]
    pub fn kv(&self) -> KVManager {
        KVManager::new(self.ctx.clone())
    }

    #[getter]
    #[must_use]
    pub fn streams(&self) -> StreamsManager {
        StreamsManager::new(self.ctx.clone())
    }
}
