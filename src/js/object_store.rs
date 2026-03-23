use std::{collections::HashMap, sync::Arc, time::Duration};

use async_nats::HeaderMap;
use pyo3::{Bound, Py, PyAny, Python, types::PyDict};
use tokio::{io::AsyncReadExt, sync::RwLock};

use crate::{
    exceptions::rust_err::NatsrpyResult,
    js::stream::{Placement, StorageType},
    utils::{
        headers::NatsrpyHeadermapExt,
        natsrpy_future,
        py_types::{SendableValue, TimeValue},
    },
};

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone)]
pub struct ObjectStoreConfig {
    pub bucket: String,
    pub description: Option<String>,
    pub max_age: Duration,
    pub max_bytes: i64,
    pub storage: StorageType,
    pub num_replicas: usize,
    pub compression: bool,
    pub placement: Option<Placement>,
}

impl From<ObjectStoreConfig> for async_nats::jetstream::object_store::Config {
    fn from(value: ObjectStoreConfig) -> Self {
        Self {
            bucket: value.bucket,
            description: value.description,
            max_age: value.max_age,
            max_bytes: value.max_bytes,
            storage: value.storage.into(),
            num_replicas: value.num_replicas,
            compression: value.compression,
            placement: value.placement.map(Into::into),
        }
    }
}

#[pyo3::pymethods]
impl ObjectStoreConfig {
    #[new]
    #[pyo3(signature=(
        bucket,
        description=None,
        max_age=None,
        max_bytes=None,
        storage=None,
        num_replicas=None,
        compression=None,
        placement=None,

    ))]
    pub fn __new__(
        bucket: String,
        description: Option<String>,
        max_age: Option<TimeValue>,
        max_bytes: Option<i64>,
        storage: Option<StorageType>,
        num_replicas: Option<usize>,
        compression: Option<bool>,
        placement: Option<Placement>,
    ) -> Self {
        Self {
            bucket,
            description,
            placement,
            max_age: max_age.map(Into::into).unwrap_or_default(),
            max_bytes: max_bytes.unwrap_or_default(),
            storage: storage.unwrap_or_default(),
            num_replicas: num_replicas.unwrap_or_default(),
            compression: compression.unwrap_or_default(),
        }
    }
}

#[pyo3::pyclass]
pub struct ObjectStore {
    object_store: Arc<RwLock<async_nats::jetstream::object_store::ObjectStore>>,
}

impl ObjectStore {
    #[must_use]
    pub fn new(object_store: async_nats::jetstream::object_store::ObjectStore) -> Self {
        Self {
            object_store: Arc::new(RwLock::new(object_store)),
        }
    }
}

#[pyo3::pymethods]
impl ObjectStore {
    #[pyo3(signature=(
        name,
        writer,
        chunk_size=24 * 1024
    ))]
    pub fn get<'py>(
        &self,
        py: Python<'py>,
        name: String,
        writer: Py<PyAny>,
        chunk_size: Option<usize>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        let arc_writer = Arc::new(writer);
        natsrpy_future(py, async move {
            let mut object = ctx_guard.read().await.get(name).await?;
            let mut buf =
                chunk_size.map_or_else(bytes::BytesMut::new, bytes::BytesMut::with_capacity);
            loop {
                let read = object.read_buf(&mut buf).await?;
                if read == 0 {
                    break;
                }
                // Buffer is cheap to clone. Since
                // it copies only pointer to memory.
                let to_write = buf.clone();
                // Writer is wrapped into Arc, so it's also
                // cheap to clone. So its fine.
                let writer_ref = arc_writer.clone();
                tokio::task::spawn_blocking(move || {
                    Python::attach(|gil| {
                        writer_ref.call_method1(gil, "write", (&to_write[..read],))
                    })
                })
                .await??;
                buf.clear();
            }
            Ok(())
        })
    }

    pub fn delete<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            ctx_guard.read().await.delete(name).await?;
            Ok(())
        })
    }

    #[pyo3(signature=(
        name,
        value,
        chunk_size=24 * 1024,
        description=None,
        headers=None,
        metadata=None,
    ))]
    pub fn put<'py>(
        &self,
        py: Python<'py>,
        name: String,
        value: SendableValue,
        chunk_size: Option<usize>,
        description: Option<String>,
        headers: Option<Bound<'py, PyDict>>,
        metadata: Option<HashMap<String, String>>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        let headers = headers.map(|val| HeaderMap::from_pydict(val)).transpose()?;
        let meta = async_nats::jetstream::object_store::ObjectMetadata {
            name,
            chunk_size,
            description,
            metadata: metadata.unwrap_or_default(),
            headers,
        };
        natsrpy_future(py, async move {
            match value {
                SendableValue::Bytes(data) => {
                    let mut reader = tokio::io::BufReader::new(&*data);
                    ctx_guard.read().await.put(meta, &mut reader).await?;
                }
                SendableValue::String(filename) => {
                    let mut reader = tokio::io::BufReader::with_capacity(
                        chunk_size.unwrap_or(200 * 1024),
                        tokio::fs::File::open(filename).await?,
                    );
                    ctx_guard.read().await.put(meta, &mut reader).await?;
                }
            }
            Ok(())
        })
    }
}

#[pyo3::pymodule(submodule, name = "object_store")]
pub mod pymod {
    #[pymodule_export]
    pub use super::{ObjectStore, ObjectStoreConfig};
}
