use std::{sync::Arc, time::Duration};

use crate::{
    js::{self, stream::StreamInfo},
    utils::{
        py_types::{SendableValue, TimeValue, ToPyDate},
        streamer::Streamer,
    },
};
use futures_util::StreamExt;
use pyo3::{
    Bound, Py, PyAny, PyRef, Python,
    types::{PyBytes, PyDateTime},
};
use tokio::sync::Mutex;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::natsrpy_future,
};

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct KVConfig {
    bucket: String,
    description: Option<String>,
    max_value_size: Option<i32>,
    history: Option<i64>,
    max_age: Option<Duration>,
    max_bytes: Option<i64>,
    storage: Option<js::stream::StorageType>,
    num_replicas: Option<usize>,
    republish: Option<js::stream::Republish>,
    mirror: Option<js::stream::Source>,
    sources: Option<Vec<js::stream::Source>>,
    mirror_direct: Option<bool>,
    compression: Option<bool>,
    placement: Option<js::stream::Placement>,
    limit_markers: Option<Duration>,
}

#[pyo3::pymethods]
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
    #[must_use]
    pub fn __new__(
        bucket: String,
        description: Option<String>,
        max_value_size: Option<i32>,
        history: Option<i64>,
        max_age: Option<TimeValue>,
        max_bytes: Option<i64>,
        storage: Option<js::stream::StorageType>,
        num_replicas: Option<usize>,
        republish: Option<js::stream::Republish>,
        mirror: Option<js::stream::Source>,
        sources: Option<Vec<js::stream::Source>>,
        mirror_direct: Option<bool>,
        compression: Option<bool>,
        placement: Option<js::stream::Placement>,
        limit_markers: Option<TimeValue>,
    ) -> Self {
        Self {
            bucket,
            description,
            max_value_size,
            history,
            max_age: max_age.map(Into::into),
            max_bytes,
            storage,
            num_replicas,
            republish,
            mirror,
            sources,
            mirror_direct,
            compression,
            placement,
            limit_markers: limit_markers.map(Into::into),
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
            max_age: value.max_age.unwrap_or_default(),
            max_bytes: value.max_bytes.unwrap_or_default(),
            storage: value.storage.unwrap_or_default().into(),
            num_replicas: value.num_replicas.unwrap_or_default(),
            republish: value.republish.map(std::convert::Into::into),
            mirror: value
                .mirror
                .map(std::convert::TryInto::try_into)
                .transpose()?,
            sources: value
                .sources
                .map(|srcs| {
                    // Collect the results of trying to convert each source, and if any conversion
                    // fails, return the error
                    srcs.into_iter()
                        .map(std::convert::TryInto::try_into)
                        .collect::<Result<Vec<_>, _>>()
                })
                // Now it's a Option<Result<_>>,
                // we transpose it to Result<Option<_>>
                .transpose()?,
            mirror_direct: value.mirror_direct.unwrap_or_default(),
            compression: value.compression.unwrap_or_default(),
            placement: value.placement.map(std::convert::Into::into),
            limit_markers: value.limit_markers,
        })
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum KVOperation {
    Put,
    Delete,
    Purge,
}

impl From<async_nats::jetstream::kv::Operation> for KVOperation {
    fn from(value: async_nats::jetstream::kv::Operation) -> Self {
        match value {
            async_nats::jetstream::kv::Operation::Put => Self::Put,
            async_nats::jetstream::kv::Operation::Purge => Self::Purge,
            async_nats::jetstream::kv::Operation::Delete => Self::Delete,
        }
    }
}

#[pyo3::pyclass(get_all)]
pub struct KVEntry {
    pub bucket: String,
    pub key: String,
    pub value: Py<PyBytes>,
    pub revision: u64,
    pub delta: u64,
    pub created: Py<PyDateTime>,
    pub operation: KVOperation,
    pub seen_current: bool,
}

#[pyo3::pymethods]
impl KVEntry {
    #[must_use]
    pub fn __repr__(&self) -> String {
        format!(
            "KVEntry<bucket={bucket:?}, key={key:?}, value={value}, revision={revision}, created={created}>",
            bucket = self.bucket,
            key = self.key,
            value = self.value,
            revision = self.revision,
            created = self.created,
        )
    }
}

impl TryFrom<async_nats::jetstream::kv::Entry> for KVEntry {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::jetstream::kv::Entry) -> Result<Self, Self::Error> {
        Ok(Self {
            bucket: value.bucket,
            key: value.key,
            value: Python::attach(|gil| PyBytes::new(gil, &value.value).unbind()),
            revision: value.revision,
            delta: value.delta,
            created: Python::attach(|gil| value.created.to_py_date(gil).map(pyo3::Bound::unbind))?,
            operation: value.operation.into(),
            seen_current: value.seen_current,
        })
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct KVStatus {
    info: StreamInfo,
    bucket: String,
}

impl TryFrom<async_nats::jetstream::kv::bucket::Status> for KVStatus {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::jetstream::kv::bucket::Status) -> Result<Self, Self::Error> {
        Ok(Self {
            info: value.info.try_into()?,
            bucket: value.bucket,
        })
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Clone)]
pub struct KeyValue {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    stream_name: String,
    #[pyo3(get)]
    prefix: String,
    #[pyo3(get)]
    put_prefix: Option<String>,
    #[pyo3(get)]
    use_jetstream_prefix: bool,
    store: Arc<async_nats::jetstream::kv::Store>,
}

impl KeyValue {
    #[must_use]
    pub fn new(store: async_nats::jetstream::kv::Store) -> Self {
        Self {
            name: store.name.clone(),
            stream_name: store.stream_name.clone(),
            prefix: store.prefix.clone(),
            put_prefix: store.put_prefix.clone(),
            use_jetstream_prefix: store.use_jetstream_prefix,
            store: Arc::new(store),
        }
    }
}

#[pyo3::pymethods]
impl KeyValue {
    pub fn get<'py>(&self, py: Python<'py>, key: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(store
                .get(key)
                .await?
                .map(|data| Python::attach(move |gil| PyBytes::new(gil, &data).unbind())))
        })
    }

    #[pyo3(signature=(key, value, ttl=None))]
    pub fn create<'py>(
        &self,
        py: Python<'py>,
        key: String,
        value: SendableValue,
        ttl: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        let data = value.into();
        natsrpy_future(py, async move {
            if let Some(ttl) = ttl {
                Ok(store.create_with_ttl(key, data, ttl.into()).await?)
            } else {
                Ok(store.create(key, data).await?)
            }
        })
    }

    #[pyo3(signature=(
        key,
        ttl=None,
        expect_revision=None,
    ))]
    pub fn purge<'py>(
        &self,
        py: Python<'py>,
        key: String,
        ttl: Option<TimeValue>,
        expect_revision: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            match (ttl, expect_revision) {
                (None, _) => Ok(store.purge_expect_revision(key, expect_revision).await?),
                (Some(ttl), None) => Ok(store.purge_with_ttl(key, ttl.into()).await?),
                (Some(ttl), Some(revision)) => Ok(store
                    .purge_expect_revision_with_ttl(key, revision, ttl.into())
                    .await?),
            }
        })
    }

    pub fn put<'py>(
        &self,
        py: Python<'py>,
        key: String,
        value: SendableValue,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        let data = value.into();
        natsrpy_future(py, async move { Ok(store.put(key, data).await?) })
    }

    #[pyo3(signature=(
        key,
        expect_revision=None,
    ))]
    pub fn delete<'py>(
        &self,
        py: Python<'py>,
        key: String,
        expect_revision: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(store.delete_expect_revision(key, expect_revision).await?)
        })
    }

    pub fn update<'py>(
        &self,
        py: Python<'py>,
        key: String,
        value: SendableValue,
        revision: u64,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(store.update(key, value.into(), revision).await?)
        })
    }

    pub fn history<'py>(&self, py: Python<'py>, key: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(KVEntryIterator::new(Streamer::new(
                store.history(key).await?,
            )))
        })
    }

    #[pyo3(signature=(from_revision=None))]
    pub fn watch_all<'py>(
        &self,
        py: Python<'py>,
        from_revision: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            let watch = if let Some(rev) = from_revision {
                store.watch_all_from_revision(rev).await?
            } else {
                store.watch_all().await?
            };
            Ok(KVEntryIterator::new(Streamer::new(watch)))
        })
    }

    #[pyo3(signature=(key, from_revision=None))]
    pub fn watch<'py>(
        &self,
        py: Python<'py>,
        key: String,
        from_revision: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            let watch = if let Some(rev) = from_revision {
                store.watch_from_revision(key, rev).await?
            } else {
                store.watch(key).await?
            };
            Ok(KVEntryIterator::new(Streamer::new(watch)))
        })
    }

    pub fn watch_with_history<'py>(
        &self,
        py: Python<'py>,
        key: String,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(KVEntryIterator::new(Streamer::new(
                store.watch_with_history(key).await?,
            )))
        })
    }

    pub fn watch_many<'py>(
        &self,
        py: Python<'py>,
        keys: Vec<String>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(KVEntryIterator::new(Streamer::new(
                store.watch_many(keys).await?,
            )))
        })
    }

    pub fn watch_many_with_history<'py>(
        &self,
        py: Python<'py>,
        keys: Vec<String>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(KVEntryIterator::new(Streamer::new(
                store.watch_many_with_history(keys).await?,
            )))
        })
    }

    #[pyo3(signature=(
        key,
        revision=None,
    ))]
    pub fn entry<'py>(
        &self,
        py: Python<'py>,
        key: String,
        revision: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            let entry = if let Some(rev) = revision {
                store
                    .entry_for_revision(key, rev)
                    .await?
                    .map(KVEntry::try_from)
                    .transpose()?
            } else {
                store.entry(key).await?.map(KVEntry::try_from).transpose()?
            };
            Ok(entry)
        })
    }

    pub fn status<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move { KVStatus::try_from(store.status().await?) })
    }

    pub fn keys<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let store = self.store.clone();
        natsrpy_future(py, async move {
            Ok(KeysIterator::new(Streamer::new(store.keys().await?)))
        })
    }
}

#[pyo3::pyclass]
pub struct KeysIterator {
    streamer: Arc<Mutex<Streamer<Result<String, async_nats::jetstream::kv::WatcherError>>>>,
}

impl KeysIterator {
    #[must_use]
    pub fn new(
        streamer: Streamer<Result<String, async_nats::jetstream::kv::WatcherError>>,
    ) -> Self {
        Self {
            streamer: Arc::new(Mutex::new(streamer)),
        }
    }
}

#[pyo3::pymethods]
impl KeysIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.streamer.clone();
        natsrpy_future(py, async move {
            let value = ctx.lock().await.next().await;
            match value {
                Some(entry) => Ok(entry?),
                None => Err(NatsrpyError::AsyncStopIteration),
            }
        })
    }
}

#[pyo3::pyclass]
pub struct KVEntryIterator {
    streamer: Arc<
        Mutex<
            Streamer<
                Result<async_nats::jetstream::kv::Entry, async_nats::jetstream::kv::WatcherError>,
            >,
        >,
    >,
}

impl KVEntryIterator {
    #[must_use]
    pub fn new(
        streamer: Streamer<
            Result<async_nats::jetstream::kv::Entry, async_nats::jetstream::kv::WatcherError>,
        >,
    ) -> Self {
        Self {
            streamer: Arc::new(Mutex::new(streamer)),
        }
    }
}

#[pyo3::pymethods]
impl KVEntryIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.streamer.clone();
        natsrpy_future(py, async move {
            let value = ctx.lock().await.next().await;
            match value {
                Some(entry) => KVEntry::try_from(entry?),
                None => Err(NatsrpyError::AsyncStopIteration),
            }
        })
    }
}

#[pyo3::pymodule(submodule, name = "kv")]
pub mod pymod {
    #[pymodule_export]
    use super::{
        KVConfig, KVEntry, KVEntryIterator, KVOperation, KVStatus, KeyValue, KeysIterator,
    };
}
