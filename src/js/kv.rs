use std::{sync::Arc, time::Duration};

use crate::js;
use pyo3::{
    Bound, PyAny, Python, pyclass, pymethods,
    types::{PyBytes, PyBytesMethods},
};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::natsrpy_future,
};

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct KVConfig {
    bucket: String,
    description: Option<String>,
    max_value_size: Option<i32>,
    history: Option<i64>,
    max_age: Option<f32>,
    max_bytes: Option<i64>,
    storage: Option<js::stream::StorageType>,
    num_replicas: Option<usize>,
    republish: Option<js::stream::Republish>,
    mirror: Option<js::stream::Source>,
    sources: Option<Vec<js::stream::Source>>,
    mirror_direct: Option<bool>,
    compression: Option<bool>,
    placement: Option<js::stream::Placement>,
    limit_markers: Option<f32>,
}

#[pymethods]
impl KVConfig {
    #[new]
    #[pyo3(signature=(
        bucket,
        description=None,
        max_value_size=None,
        history=None,
        max_age=None,
        max_bytes=None,
        storage=None,
        num_replicas=None,
        republish=None,
        mirror=None,
        sources=None,
        mirror_direct=None,
        compression=None,
        placement=None,
        limit_markers=None,
    ))]
    pub fn __new__(
        bucket: String,
        description: Option<String>,
        max_value_size: Option<i32>,
        history: Option<i64>,
        max_age: Option<f32>,
        max_bytes: Option<i64>,
        storage: Option<js::stream::StorageType>,
        num_replicas: Option<usize>,
        republish: Option<js::stream::Republish>,
        mirror: Option<js::stream::Source>,
        sources: Option<Vec<js::stream::Source>>,
        mirror_direct: Option<bool>,
        compression: Option<bool>,
        placement: Option<js::stream::Placement>,
        limit_markers: Option<f32>,
    ) -> Self {
        Self {
            bucket,
            description,
            max_value_size,
            history,
            max_age,
            max_bytes,
            storage,
            num_replicas,
            republish,
            mirror,
            sources,
            mirror_direct,
            compression,
            placement,
            limit_markers,
        }
    }
}

impl TryFrom<KVConfig> for async_nats::jetstream::kv::Config {
    type Error = NatsrpyError;

    fn try_from(value: KVConfig) -> Result<Self, Self::Error> {
        Ok(Self {
            bucket: value.bucket,
            description: value.description.unwrap_or_default(),
            max_value_size: value.max_value_size.unwrap_or_default(),
            history: value.history.unwrap_or_default(),
            max_age: value
                .max_age
                .map(|val| std::time::Duration::from_secs_f32(val))
                .unwrap_or_default(),
            max_bytes: value.max_bytes.unwrap_or_default(),
            storage: value.storage.unwrap_or_default().into(),
            num_replicas: value.num_replicas.unwrap_or_default(),
            republish: value.republish.map(|r| r.into()),
            mirror: value.mirror.map(|m| m.try_into()).transpose()?,
            sources: value
                .sources
                .map(|srcs| {
                    // Collect the results of trying to convert each source, and if any conversion
                    // fails, return the error
                    srcs.into_iter()
                        .map(|s| s.try_into())
                        .collect::<Result<Vec<_>, _>>()
                })
                // Now it's a Option<Result<_>>,
                // we transpose it to Result<Option<_>>
                .transpose()?,
            mirror_direct: value.mirror_direct.unwrap_or_default(),
            compression: value.compression.unwrap_or_default(),
            placement: value.placement.map(|p| p.into()),
            limit_markers: value.limit_markers.map(|val| Duration::from_secs_f32(val)),
        })
    }
}

#[pyclass]
pub struct KeyValue {
    store: Arc<RwLock<async_nats::jetstream::kv::Store>>,
}

impl KeyValue {
    pub fn new(store: async_nats::jetstream::kv::Store) -> Self {
        Self {
            store: Arc::new(RwLock::new(store)),
        }
    }
}

#[pymethods]
impl KeyValue {
    pub fn get<'py>(&self, py: Python<'py>, key: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            let kv = store.read().await;
            if let Some(data) = kv.get(key).await? {
                let pybytes = Python::attach(move |gil| PyBytes::new(gil, &data).unbind());
                Ok(Some(pybytes))
            } else {
                Ok(None)
            }
        })
    }

    pub fn put<'py>(
        &self,
        py: Python<'py>,
        key: String,
        value: Bound<'py, PyBytes>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        let data = bytes::Bytes::copy_from_slice(value.as_bytes());
        natsrpy_future(py, async move {
            let kv = store.read().await;
            let status = kv.put(key, data).await?;
            Ok(status)
        })
    }

    pub fn delete<'py>(&self, py: Python<'py>, key: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            let kv = store.read().await;
            Ok(kv.delete(key).await?)
        })
    }
}

#[pyo3::pymodule(submodule, name = "kv")]
pub mod pymod {
    #[pymodule_export]
    use super::{KVConfig, KeyValue};
}
