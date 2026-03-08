use std::ops::Deref;
use std::sync::Arc;
use std::time::Duration;

use async_nats::Subject;
use async_nats::client::traits::Publisher;
use async_nats::connection::State;
use pyo3::types::{PyBytesMethods, PyDict};
use pyo3::{Bound, PyAny, Python, pyclass, pymethods, types::PyBytes};
use tokio::sync::RwLock;

use crate::exceptions::rust_err::NatsrpyError;
use crate::jetstream::kv::KeyValue;
use crate::utils::headers::NatsrpyHeadermapExt;
use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

#[pyclass]
pub enum StorageType {
    File,
    Memory,
}

impl From<&StorageType> for async_nats::jetstream::stream::StorageType {
    fn from(value: &StorageType) -> Self {
        match value {
            StorageType::File => Self::File,
            StorageType::Memory => Self::Memory,
        }
    }
}

#[pyclass]
pub struct Republish {
    pub source: String,
    pub destination: String,
    pub headers_only: bool,
}
impl From<&Republish> for async_nats::jetstream::stream::Republish {
    fn from(value: &Republish) -> Self {
        Self {
            source: value.source.clone(),
            destination: value.destination.clone(),
            headers_only: value.headers_only.clone(),
        }
    }
}

#[pyclass]
pub struct Source {
    pub name: String,
    pub filter_subject: Option<String>,
    pub external: bool,
}

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
        bucket: String,
        description: Option<String>,
        max_value_size: Option<i32>,
        history: Option<i64>,
        max_age: Option<f32>,
        max_bytes: Option<i64>,
        storage: Option<Bound<'a, StorageType>>,
        num_replicas: Option<usize>,
        republish: Option<Bound<'a, Republish>>,
        mirror: Option<Bound<'a, Source>>,
        // sources: Option<Vec<Source>>,
        mirror_direct: Option<bool>,
        compression: Option<bool>,
        // placement: Option<Place>,
        limit_markers: Option<f32>,
    ) -> NatsrpyResult<Bound<'a, PyAny>> {
        let ctx = self.ctx.clone();
        let storage = storage.map(|val| val.borrow().deref().into());
        let republish = republish.map(|val| val.borrow().deref().into());
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            let mut config = async_nats::jetstream::kv::Config {
                bucket: bucket.clone(),
                ..Default::default()
            };
            description
                .into_iter()
                .for_each(|descr| config.description = descr);
            max_value_size
                .into_iter()
                .for_each(|val| config.max_value_size = val);
            history.into_iter().for_each(|val| config.history = val);
            max_age
                .into_iter()
                .for_each(|val| config.max_age = Duration::from_secs_f32(val));
            max_bytes.into_iter().for_each(|val| config.max_bytes = val);
            num_replicas
                .into_iter()
                .for_each(|val| config.num_replicas = val);
            mirror_direct
                .into_iter()
                .for_each(|val| config.mirror_direct = val);
            compression
                .into_iter()
                .for_each(|val| config.compression = val);
            storage.into_iter().for_each(|val| config.storage = val);
            config.republish = republish;
            config.limit_markers = limit_markers.map(Duration::from_secs_f32);

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
}
