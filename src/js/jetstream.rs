use std::ops::Deref;
use std::sync::Arc;

use async_nats::Subject;
use async_nats::client::traits::Publisher;
use async_nats::connection::State;
use pyo3::types::{PyBytesMethods, PyDict};
use pyo3::{Bound, PyAny, Python, pyclass, pymethods, types::PyBytes};
use tokio::sync::RwLock;

use crate::exceptions::rust_err::NatsrpyError;
use crate::js::kv::{KVConfig, KeyValue};
use crate::utils::headers::NatsrpyHeadermapExt;
use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

#[pyclass]
pub struct JetStream {
    ctx: Arc<RwLock<async_nats::jetstream::Context>>,
}

impl JetStream {
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
    pub fn publish<'a>(
        &self,
        py: Python<'a>,
        subject: String,
        payload: Bound<PyBytes>,
        headers: Option<Bound<PyDict>>,
        reply: Option<String>,
        err_on_disconnect: bool,
    ) -> NatsrpyResult<Bound<'a, PyAny>> {
        let ctx = self.ctx.clone();
        let data = bytes::Bytes::from(payload.as_bytes().to_vec());
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            if err_on_disconnect && js.client().connection_state() == State::Disconnected {
                return Err(NatsrpyError::Disconnected);
            }
            js.publish_message(async_nats::message::OutboundMessage {
                subject: Subject::from(subject),
                payload: data,
                headers: headermap,
                reply: reply.map(Subject::from),
            })
            .await?;
            Ok(())
        })
    }

    pub fn create_kv<'a>(
        &self,
        py: Python<'a>,
        config: Bound<'a, KVConfig>,
    ) -> NatsrpyResult<Bound<'a, PyAny>> {
        let ctx = self.ctx.clone();
        let config = config.borrow().deref().clone().try_into()?;

        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(KeyValue::new(js.create_key_value(config).await?))
        })
    }

    pub fn get_kv<'a>(&self, py: Python<'a>, bucket: String) -> NatsrpyResult<Bound<'a, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(KeyValue::new(js.get_key_value(bucket).await?))
        })
    }

    pub fn update_kv<'a>(
        &self,
        py: Python<'a>,
        config: Bound<'a, KVConfig>,
    ) -> NatsrpyResult<Bound<'a, PyAny>> {
        let ctx = self.ctx.clone();
        let config = config.borrow().deref().clone().try_into()?;
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(KeyValue::new(js.update_key_value(config).await?))
        })
    }
}
