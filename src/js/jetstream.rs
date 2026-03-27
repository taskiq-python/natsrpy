use std::sync::Arc;

use async_nats::{Subject, connection::State, jetstream::context::traits::Publisher};
use pyo3::{Bound, PyAny, Python, types::PyDict};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::managers::{
        counters::CountersManager, kv::KVManager, object_store::ObjectStoreManager,
        streams::StreamsManager,
    },
    utils::{headers::NatsrpyHeadermapExt, natsrpy_future, py_types::SendableValue},
};

#[pyo3::pyclass]
pub struct JetStream {
    ctx: Arc<async_nats::jetstream::Context>,
}

impl JetStream {
    #[must_use]
    pub fn new(ctx: async_nats::jetstream::Context) -> Self {
        Self { ctx: Arc::new(ctx) }
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Clone, Debug)]
pub struct Publication {
    pub stream: String,
    pub sequence: u64,
    pub domain: String,
    pub duplicate: bool,
    pub value: Option<String>,
}

impl From<async_nats::jetstream::publish::PublishAck> for Publication {
    fn from(value: async_nats::jetstream::publish::PublishAck) -> Self {
        Self {
            stream: value.stream,
            sequence: value.sequence,
            domain: value.domain,
            duplicate: value.duplicate,
            value: value.value,
        }
    }
}

#[pyo3::pymethods]
impl JetStream {
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

    #[getter]
    #[must_use]
    pub fn object_store(&self) -> ObjectStoreManager {
        ObjectStoreManager::new(self.ctx.clone())
    }

    #[getter]
    #[must_use]
    pub fn counters(&self) -> CountersManager {
        CountersManager::new(self.ctx.clone())
    }

    #[pyo3(signature = (
        subject,
        payload,
        *,
        headers=None,
        err_on_disconnect = false,
        wait = false,
    ))]
    pub fn publish<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        payload: SendableValue,
        headers: Option<Bound<PyDict>>,
        err_on_disconnect: bool,
        wait: bool,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let data = payload.into();
        let headermap = headers
            .map(async_nats::HeaderMap::from_pydict)
            .transpose()?;
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            if err_on_disconnect && client.client().connection_state() == State::Disconnected {
                return Err(NatsrpyError::Disconnected);
            }
            let publication = client
                .publish_message(async_nats::jetstream::message::OutboundMessage {
                    subject: Subject::from(subject),
                    payload: data,
                    headers: headermap,
                })
                .await?;

            if wait {
                Ok(Some(Publication::from(publication.await?)))
            } else {
                Ok(None)
            }
        })
    }
}
