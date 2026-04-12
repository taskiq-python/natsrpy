use futures_util::StreamExt;
use std::{collections::HashMap, sync::Arc, time::Duration};

use async_nats::HeaderMap;
use pyo3::{
    Bound, Py, PyAny, PyRef, Python,
    types::{IntoPyDict, PyDateTime, PyDict},
};
use tokio::{
    io::AsyncReadExt,
    sync::{Mutex, RwLock},
};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::stream::{Placement, StorageType},
    utils::{
        headers::NatsrpyHeadermapExt,
        natsrpy_future,
        py_types::{TimeValue, ToPyDate},
        streamer::Streamer,
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

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct ObjectLink {
    pub name: Option<String>,
    pub bucket: String,
}

#[pyo3::pyclass(get_all)]
#[derive(Debug)]
pub struct ObjectInfo {
    pub name: String,
    pub description: Option<String>,
    pub metadata: Py<PyDict>,
    pub headers: Py<PyDict>,
    pub bucket: String,
    pub nuid: String,
    pub size: usize,
    pub chunks: usize,
    pub modified: Option<Py<PyDateTime>>,
    pub digest: Option<String>,
    pub deleted: bool,

    pub link: Option<ObjectLink>,
    pub max_chunk_size: Option<usize>,
}

impl From<async_nats::jetstream::object_store::ObjectLink> for ObjectLink {
    fn from(value: async_nats::jetstream::object_store::ObjectLink) -> Self {
        Self {
            name: value.name,
            bucket: value.bucket,
        }
    }
}

impl TryFrom<async_nats::jetstream::object_store::ObjectInfo> for ObjectInfo {
    type Error = NatsrpyError;

    fn try_from(
        value: async_nats::jetstream::object_store::ObjectInfo,
    ) -> Result<Self, Self::Error> {
        Ok(Self {
            name: value.name,
            description: value.description,
            metadata: Python::attach(|gil| {
                value.metadata.into_py_dict(gil).map(pyo3::Bound::unbind)
            })?,
            headers: value
                .headers
                // To PyResul<Bound<'_, PyDict>> and then to PyResul<Py<PyDict>>
                .map(|val| Python::attach(|gil| val.to_pydict(gil).map(pyo3::Bound::unbind)))
                .transpose()?
                .unwrap_or_else(|| Python::attach(|gil| PyDict::new(gil).unbind())),
            bucket: value.bucket,
            nuid: value.nuid,
            size: value.size,
            chunks: value.chunks,
            modified: value
                .modified
                // To PyResul<Bound<'_, PyDateTime>> and then to PyResul<Py<PyDateTime>>
                .map(|dt| Python::attach(|gil| dt.to_py_date(gil).map(pyo3::Bound::unbind)))
                .transpose()?,
            digest: value.digest,
            deleted: value.deleted,
            link: value
                .options
                .as_ref()
                .and_then(|opts| opts.link.as_ref().map(|link| link.clone().into())),
            max_chunk_size: value.options.and_then(|opts| opts.max_chunk_size),
        })
    }
}

#[pyo3::pymethods]
impl ObjectInfo {
    pub fn __str__(&self) -> String {
        format!(
            "ObjectInfo<name={:?}, bucket={:?}, size={}, modified={:?}, description={:?}>",
            self.name,
            self.bucket,
            self.size,
            self.modified
                .as_ref()
                .map_or_else(|| String::from("None"), ToString::to_string),
            self.description,
        )
    }
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
        value: Vec<u8>,
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
            let mut reader = tokio::io::BufReader::new(value.as_slice());
            ctx_guard.read().await.put(meta, &mut reader).await?;
            Ok(())
        })
    }

    #[pyo3(signature=(
        name,
        path,
        chunk_size=None,
        description=None,
        headers=None,
        metadata=None,
    ))]
    pub fn put_file<'py>(
        &self,
        py: Python<'py>,
        name: String,
        path: std::path::PathBuf,
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
            let mut reader = tokio::io::BufReader::with_capacity(
                chunk_size.unwrap_or(200 * 1024),
                tokio::fs::File::open(path).await?,
            );
            ctx_guard.read().await.put(meta, &mut reader).await?;
            Ok(())
        })
    }

    #[pyo3(signature=(
        name,
        new_name=None,
        description=None,
        headers=None,
        metadata=None,
    ))]
    pub fn update_metadata<'py>(
        &self,
        py: Python<'py>,
        name: String,
        new_name: Option<String>,
        description: Option<String>,
        headers: Option<Bound<'py, PyDict>>,
        metadata: Option<HashMap<String, String>>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        let headers = headers.map(|val| HeaderMap::from_pydict(val)).transpose()?;
        let meta = async_nats::jetstream::object_store::UpdateMetadata {
            name: new_name.unwrap_or_else(|| name.clone()),
            description,
            metadata: metadata.unwrap_or_default(),
            headers,
        };
        natsrpy_future(py, async move {
            ObjectInfo::try_from(ctx_guard.read().await.update_metadata(name, meta).await?)
        })
    }

    pub fn seal<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            ctx_guard.write().await.seal().await?;
            Ok(())
        })
    }

    pub fn get_info<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            let info = ctx_guard.write().await.info(name).await?;
            ObjectInfo::try_from(info)
        })
    }

    #[pyo3(signature=(with_history=false))]
    pub fn watch<'py>(
        &self,
        py: Python<'py>,
        with_history: bool,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            let watcher = if with_history {
                ctx_guard.read().await.watch_with_history().await?
            } else {
                ctx_guard.read().await.watch().await?
            };
            Ok(ObjectInfoIterator::new(Streamer::new(watcher)))
        })
    }

    pub fn list<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            Ok(ObjectInfoIterator::new(Streamer::new(
                ctx_guard.read().await.list().await?,
            )))
        })
    }

    pub fn link_bucket<'py>(
        &self,
        py: Python<'py>,
        src_bucket: String,
        dest: String,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            ObjectInfo::try_from(
                ctx_guard
                    .read()
                    .await
                    .add_bucket_link(dest, src_bucket)
                    .await?,
            )
        })
    }

    pub fn link_object<'py>(
        &self,
        py: Python<'py>,
        src: String,
        dest: String,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.object_store.clone();
        natsrpy_future(py, async move {
            let target = ctx_guard.read().await.get(src).await?;
            ObjectInfo::try_from(ctx_guard.read().await.add_link(dest, &target.info).await?)
        })
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Clone, Debug)]
pub struct ObjectInfoIterator {
    streamer: Arc<
        Mutex<
            Streamer<
                Result<
                    async_nats::jetstream::object_store::ObjectInfo,
                    async_nats::jetstream::object_store::WatcherError,
                >,
            >,
        >,
    >,
}

impl ObjectInfoIterator {
    #[must_use]
    pub fn new(
        streamer: Streamer<
            Result<
                async_nats::jetstream::object_store::ObjectInfo,
                async_nats::jetstream::object_store::WatcherError,
            >,
        >,
    ) -> Self {
        Self {
            streamer: Arc::new(Mutex::new(streamer)),
        }
    }
}

#[pyo3::pymethods]
impl ObjectInfoIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.streamer.clone();
        natsrpy_future(py, async move {
            let value = ctx.lock().await.next().await;
            match value {
                Some(info) => ObjectInfo::try_from(info?),
                None => Err(NatsrpyError::AsyncStopIteration),
            }
        })
    }
}

#[pyo3::pymodule(submodule, name = "object_store")]
pub mod pymod {
    #[pymodule_export]
    pub use super::{ObjectInfo, ObjectInfoIterator, ObjectLink, ObjectStore, ObjectStoreConfig};
}
