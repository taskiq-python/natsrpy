use std::sync::Arc;

use pyo3::{
    Bound, PyAny, Python, pyclass, pymethods,
    types::{PyBytes, PyBytesMethods},
};
use tokio::sync::RwLock;

use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

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
    pub fn get<'a>(&self, py: Python<'a>, key: String) -> NatsrpyResult<Bound<'a, PyAny>> {
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

    pub fn put<'a>(
        &self,
        py: Python<'a>,
        key: String,
        value: Bound<'a, PyBytes>,
    ) -> NatsrpyResult<Bound<'a, PyAny>> {
        let store = self.store.clone();
        let data = bytes::Bytes::copy_from_slice(value.as_bytes());
        natsrpy_future(py, async move {
            let kv = store.read().await;
            let status = kv.put(key, data).await?;
            Ok(status)
        })
    }
}
