use pyo3::{
    Py,
    types::{PyBytes, PyDateTime, PyTzInfo},
};
use std::{collections::HashMap, ops::Deref, sync::Arc, time::Duration};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::{headers::NatsrpyHeadermapExt, natsrpy_future},
};
use pyo3::{Bound, PyAny, Python, pyclass, pymethods, types::PyDict};

#[pyclass(from_py_object)]
#[derive(Clone, Copy, Default, PartialEq, Eq)]
pub enum StorageType {
    #[default]
    FILE,
    MEMORY,
}

impl From<StorageType> for async_nats::jetstream::stream::StorageType {
    fn from(value: StorageType) -> Self {
        match value {
            StorageType::FILE => Self::File,
            StorageType::MEMORY => Self::Memory,
        }
    }
}

#[pyclass(from_py_object)]
#[derive(Clone, Copy, Default, PartialEq, Eq)]
pub enum DiscardPolicy {
    #[default]
    OLD,
    NEW,
}

impl From<DiscardPolicy> for async_nats::jetstream::stream::DiscardPolicy {
    fn from(value: DiscardPolicy) -> Self {
        match value {
            DiscardPolicy::OLD => Self::Old,
            DiscardPolicy::NEW => Self::New,
        }
    }
}

#[pyclass(from_py_object)]
#[derive(Clone, Copy, Default, PartialEq, Eq)]
pub enum RetentionPolicy {
    #[default]
    LIMITS,
    INTEREST,
    WORKQUEUE,
}

impl From<RetentionPolicy> for async_nats::jetstream::stream::RetentionPolicy {
    fn from(value: RetentionPolicy) -> Self {
        match value {
            RetentionPolicy::LIMITS => Self::Limits,
            RetentionPolicy::INTEREST => Self::Interest,
            RetentionPolicy::WORKQUEUE => Self::WorkQueue,
        }
    }
}

#[pyclass(from_py_object)]
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Compression {
    S2,
    NONE,
}

impl From<Compression> for async_nats::jetstream::stream::Compression {
    fn from(value: Compression) -> Self {
        match value {
            Compression::S2 => Self::S2,
            Compression::NONE => Self::None,
        }
    }
}

#[pyclass(from_py_object)]
#[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
pub enum PersistenceMode {
    #[default]
    Default,
    Async,
}

impl From<PersistenceMode> for async_nats::jetstream::stream::PersistenceMode {
    fn from(value: PersistenceMode) -> Self {
        match value {
            PersistenceMode::Default => Self::Default,
            PersistenceMode::Async => Self::Async,
        }
    }
}

#[pyclass(from_py_object)]
#[derive(Clone, Debug, PartialEq, Eq, Default)]
pub struct ConsumerLimits {
    pub inactive_threshold: Duration,
    pub max_ack_pending: i64,
}

#[pymethods]
impl ConsumerLimits {
    #[new]
    #[must_use]
    pub const fn __new__(inactive_threshold: Duration, max_ack_pending: i64) -> Self {
        Self {
            inactive_threshold,
            max_ack_pending,
        }
    }
}

impl From<ConsumerLimits> for async_nats::jetstream::stream::ConsumerLimits {
    fn from(value: ConsumerLimits) -> Self {
        Self {
            inactive_threshold: value.inactive_threshold,
            max_ack_pending: value.max_ack_pending,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct Republish {
    pub source: String,
    pub destination: String,
    pub headers_only: bool,
}

#[pymethods]
impl Republish {
    #[new]
    #[must_use]
    pub const fn __new__(source: String, destination: String, headers_only: bool) -> Self {
        Self {
            source,
            destination,
            headers_only,
        }
    }
}

impl From<Republish> for async_nats::jetstream::stream::Republish {
    fn from(value: Republish) -> Self {
        Self {
            source: value.source.clone(),
            destination: value.destination.clone(),
            headers_only: value.headers_only,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct External {
    pub api_prefix: String,
    pub delivery_prefix: Option<String>,
}

#[pymethods]
impl External {
    #[new]
    #[pyo3(signature = (api_prefix, delivery_prefix=None))]
    #[must_use]
    pub const fn __new__(api_prefix: String, delivery_prefix: Option<String>) -> Self {
        Self {
            api_prefix,
            delivery_prefix,
        }
    }
}

impl From<&External> for async_nats::jetstream::stream::External {
    fn from(value: &External) -> Self {
        Self {
            api_prefix: value.api_prefix.clone(),
            delivery_prefix: value.delivery_prefix.clone(),
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct SubjectTransform {
    pub source: String,
    pub destination: String,
}

impl From<SubjectTransform> for async_nats::jetstream::stream::SubjectTransform {
    fn from(value: SubjectTransform) -> Self {
        Self {
            source: value.source,
            destination: value.destination,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct Source {
    pub name: String,
    pub filter_subject: Option<String>,
    pub external: Option<External>,
    pub start_sequence: Option<u64>,
    pub start_time: Option<i64>,
    pub domain: Option<String>,
    pub subject_transforms: Vec<SubjectTransform>,
}

impl TryFrom<Source> for async_nats::jetstream::stream::Source {
    type Error = NatsrpyError;

    fn try_from(value: Source) -> Result<Self, Self::Error> {
        Ok(Self {
            name: value.name.clone(),
            filter_subject: value.filter_subject.clone(),
            external: value.external.as_ref().map(std::convert::Into::into),
            start_sequence: value.start_sequence,
            start_time: value
                .start_time
                .map(time::OffsetDateTime::from_unix_timestamp)
                .transpose()?,
            domain: value.domain.clone(),
            subject_transforms: value
                .subject_transforms
                .into_iter()
                .map(std::convert::Into::into)
                .collect(),
        })
    }
}

#[pymethods]
impl Source {
    #[new]
    #[pyo3(signature = (
        name,
        filter_subject=None,
        external=None,
        start_sequence = None,
        start_time=None,
        domain=None,
        subject_transforms = vec![]
    ))]
    pub fn __new__(
        name: String,
        filter_subject: Option<String>,
        external: Option<Bound<'_, External>>,
        start_sequence: Option<u64>,
        start_time: Option<i64>,
        domain: Option<String>,
        subject_transforms: Vec<Bound<'_, SubjectTransform>>,
    ) -> NatsrpyResult<Self> {
        Ok(Self {
            name,
            domain,
            start_time,
            start_sequence,
            filter_subject,
            subject_transforms: subject_transforms
                .into_iter()
                .map(|val| val.borrow().deref().clone())
                .collect(),
            external: external.map(|e| e.borrow().deref().clone()),
        })
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct Placement {
    pub cluster: Option<String>,
    pub tags: Vec<String>,
}

#[pymethods]
impl Placement {
    #[new]
    #[pyo3(signature=(cluster=None, tags=None))]
    #[must_use]
    pub fn __new__(cluster: Option<String>, tags: Option<Vec<String>>) -> Self {
        Self {
            cluster,
            tags: tags.unwrap_or_default(),
        }
    }
}

impl From<Placement> for async_nats::jetstream::stream::Placement {
    fn from(value: Placement) -> Self {
        Self {
            cluster: value.cluster,
            tags: value.tags,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct StreamConfig {
    pub name: String,
    pub subjects: Vec<String>,
    pub max_bytes: Option<i64>,
    pub max_messages: Option<i64>,
    pub max_messages_per_subject: Option<i64>,
    pub discard: Option<DiscardPolicy>,
    pub discard_new_per_subject: Option<bool>,
    pub retention: Option<RetentionPolicy>,
    pub max_consumers: Option<i32>,
    pub max_age: Option<Duration>,
    pub max_message_size: Option<i32>,
    pub storage: Option<StorageType>,
    pub num_replicas: Option<usize>,
    pub no_ack: Option<bool>,
    pub duplicate_window: Option<Duration>,
    pub template_owner: Option<String>,
    pub sealed: Option<bool>,
    pub description: Option<String>,
    pub allow_rollup: Option<bool>,
    pub deny_delete: Option<bool>,
    pub deny_purge: Option<bool>,
    pub republish: Option<Republish>,
    pub allow_direct: Option<bool>,
    pub mirror_direct: Option<bool>,
    pub mirror: Option<Source>,
    pub sources: Option<Vec<Source>>,
    pub metadata: Option<HashMap<String, String>>,
    pub subject_transform: Option<SubjectTransform>,
    pub compression: Option<Compression>,
    pub consumer_limits: Option<ConsumerLimits>,
    pub first_sequence: Option<u64>,
    pub placement: Option<Placement>,
    pub persist_mode: Option<PersistenceMode>,
    pub pause_until: Option<i64>,
    pub allow_message_ttl: Option<bool>,
    pub subject_delete_marker_ttl: Option<Duration>,
    pub allow_atomic_publish: Option<bool>,
    pub allow_message_schedules: Option<bool>,
    pub allow_message_counter: Option<bool>,
}

#[pymethods]
impl StreamConfig {
    #[new]
    #[pyo3(signature=(
        name,
        subjects,
        max_bytes=None,
        max_messages=None,
        max_messages_per_subject=None,
        discard=None,
        discard_new_per_subject=None,
        retention=None,
        max_consumers=None,
        max_age=None,
        max_message_size=None,
        storage=None,
        num_replicas=None,
        no_ack=None,
        duplicate_window=None,
        template_owner=None,
        sealed=None,
        description=None,
        allow_rollup=None,
        deny_delete=None,
        deny_purge=None,
        republish=None,
        allow_direct=None,
        mirror_direct=None,
        mirror=None,
        sources=None,
        metadata=None,
        subject_transform=None,
        compression=None,
        consumer_limits=None,
        first_sequence=None,
        placement=None,
        persist_mode=None,
        pause_until=None,
        allow_message_ttl=None,
        subject_delete_marker_ttl=None,
        allow_atomic_publish=None,
        allow_message_schedules=None,
        allow_message_counter=None,
    ))]
    pub const fn __new__(
        name: String,
        subjects: Vec<String>,
        max_bytes: Option<i64>,
        max_messages: Option<i64>,
        max_messages_per_subject: Option<i64>,
        discard: Option<DiscardPolicy>,
        discard_new_per_subject: Option<bool>,
        retention: Option<RetentionPolicy>,
        max_consumers: Option<i32>,
        max_age: Option<Duration>,
        max_message_size: Option<i32>,
        storage: Option<StorageType>,
        num_replicas: Option<usize>,
        no_ack: Option<bool>,
        duplicate_window: Option<Duration>,
        template_owner: Option<String>,
        sealed: Option<bool>,
        description: Option<String>,
        allow_rollup: Option<bool>,
        deny_delete: Option<bool>,
        deny_purge: Option<bool>,
        republish: Option<Republish>,
        allow_direct: Option<bool>,
        mirror_direct: Option<bool>,
        mirror: Option<Source>,
        sources: Option<Vec<Source>>,
        metadata: Option<HashMap<String, String>>,
        subject_transform: Option<SubjectTransform>,
        compression: Option<Compression>,
        consumer_limits: Option<ConsumerLimits>,
        first_sequence: Option<u64>,
        placement: Option<Placement>,
        persist_mode: Option<PersistenceMode>,
        pause_until: Option<i64>,
        allow_message_ttl: Option<bool>,
        subject_delete_marker_ttl: Option<Duration>,
        allow_atomic_publish: Option<bool>,
        allow_message_schedules: Option<bool>,
        allow_message_counter: Option<bool>,
    ) -> NatsrpyResult<Self> {
        Ok(Self {
            name,
            subjects,
            max_bytes,
            max_messages,
            max_messages_per_subject,
            discard,
            discard_new_per_subject,
            retention,
            max_consumers,
            max_age,
            max_message_size,
            storage,
            num_replicas,
            no_ack,
            duplicate_window,
            template_owner,
            sealed,
            description,
            allow_rollup,
            deny_delete,
            deny_purge,
            republish,
            allow_direct,
            mirror_direct,
            mirror,
            sources,
            metadata,
            subject_transform,
            compression,
            consumer_limits,
            first_sequence,
            placement,
            persist_mode,
            pause_until,
            allow_message_ttl,
            subject_delete_marker_ttl,
            allow_atomic_publish,
            allow_message_schedules,
            allow_message_counter,
        })
    }
}

impl TryFrom<StreamConfig> for async_nats::jetstream::stream::Config {
    type Error = NatsrpyError;

    fn try_from(value: StreamConfig) -> Result<Self, Self::Error> {
        let mut conf = Self {
            name: value.name,
            subjects: value.subjects,
            description: value.description,
            first_sequence: value.first_sequence,
            subject_delete_marker_ttl: value.subject_delete_marker_ttl,
            ..Default::default()
        };

        // Optional values that have defaults.
        // If the value is not present, we just use the one
        // that nats' config defaults to.
        conf.max_bytes = value.max_bytes.unwrap_or(conf.max_bytes);
        conf.max_messages = value.max_messages.unwrap_or(conf.max_messages);
        conf.max_messages_per_subject = value
            .max_messages_per_subject
            .unwrap_or(conf.max_messages_per_subject);
        conf.discard_new_per_subject = value
            .discard_new_per_subject
            .unwrap_or(conf.discard_new_per_subject);
        conf.max_consumers = value.max_consumers.unwrap_or(conf.max_consumers);
        conf.max_age = value.max_age.unwrap_or(conf.max_age);
        conf.max_message_size = value.max_message_size.unwrap_or(conf.max_message_size);
        conf.num_replicas = value.num_replicas.unwrap_or(conf.num_replicas);
        conf.no_ack = value.no_ack.unwrap_or(conf.no_ack);
        conf.duplicate_window = value.duplicate_window.unwrap_or(conf.duplicate_window);
        conf.template_owner = value.template_owner.unwrap_or(conf.template_owner);
        conf.sealed = value.sealed.unwrap_or(conf.sealed);
        conf.allow_rollup = value.allow_rollup.unwrap_or(conf.allow_rollup);
        conf.deny_delete = value.deny_delete.unwrap_or(conf.deny_delete);
        conf.deny_purge = value.deny_purge.unwrap_or(conf.deny_purge);
        conf.allow_direct = value.allow_direct.unwrap_or(conf.allow_direct);
        conf.mirror_direct = value.mirror_direct.unwrap_or(conf.mirror_direct);
        conf.metadata = value.metadata.unwrap_or(conf.metadata);
        conf.allow_message_ttl = value.allow_message_ttl.unwrap_or(conf.allow_message_ttl);
        conf.allow_atomic_publish = value
            .allow_atomic_publish
            .unwrap_or(conf.allow_atomic_publish);
        conf.allow_message_schedules = value
            .allow_message_schedules
            .unwrap_or(conf.allow_message_schedules);
        conf.allow_message_counter = value
            .allow_message_counter
            .unwrap_or(conf.allow_message_counter);

        // Values that require conversion between python -> rust types.
        conf.republish = value.republish.map(Into::into);
        conf.storage = value.storage.map_or(conf.storage, Into::into);
        conf.retention = value.retention.map_or(conf.retention, Into::into);
        conf.discard = value.discard.map_or(conf.discard, Into::into);
        conf.mirror = value.mirror.map(TryInto::try_into).transpose()?;
        conf.sources = value
            .sources
            .map(|sources| {
                sources
                    .into_iter()
                    .map(TryInto::try_into)
                    .collect::<Result<Vec<_>, _>>()
            })
            .transpose()?;
        conf.subject_transform = value.subject_transform.map(Into::into);
        conf.compression = value.compression.map(Into::into);
        conf.consumer_limits = value.consumer_limits.map(Into::into);
        conf.placement = value.placement.map(Into::into);
        conf.persist_mode = value.persist_mode.map(Into::into);
        conf.pause_until = value
            .pause_until
            .map(time::OffsetDateTime::from_unix_timestamp)
            .transpose()?;

        Ok(conf)
    }
}

#[pyclass(get_all)]
#[derive(Debug)]
pub struct StreamMessage {
    pub subject: String,
    pub sequence: u64,
    pub headers: Py<PyDict>,
    pub payload: Py<PyBytes>,
    pub time: Py<PyDateTime>,
}

impl StreamMessage {
    pub fn from_nats_message(
        py: Python,
        msg: async_nats::jetstream::message::StreamMessage,
    ) -> NatsrpyResult<Self> {
        let time = msg.time.to_utc();
        let tz_info = PyTzInfo::utc(py)?;
        let time = PyDateTime::new(
            py,
            time.year(),
            time.month().into(),
            time.day(),
            time.hour(),
            time.minute(),
            time.second(),
            time.microsecond(),
            Some(&*tz_info),
        )?;
        Ok(Self {
            subject: msg.subject.to_string(),
            payload: PyBytes::new(py, &msg.payload).unbind(),
            headers: msg.headers.to_pydict(py)?,
            sequence: msg.sequence,
            time: time.unbind(),
        })
    }
}

#[pymethods]
impl StreamMessage {
    #[must_use]
    pub fn __repr__(&self) -> String {
        format!(
            r#"StreamMessage<subject="{subject}", sequence={sequence}, payload={payload}, headers={headers}>"#,
            subject = self.subject,
            sequence = self.sequence,
            payload = self.payload,
            headers = self.headers,
        )
    }
}

#[pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct Stream {
    stream: Arc<RwLock<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>>,
}
impl Stream {
    #[must_use]
    pub fn new(
        stream: async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>,
    ) -> Self {
        Self {
            stream: Arc::new(RwLock::new(stream)),
        }
    }
}

#[pymethods]
impl Stream {
    pub fn direct_get<'py>(
        &self,
        py: Python<'py>,
        sequence: u64,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            let message = ctx.read().await.direct_get(sequence).await?;
            let result = Python::attach(move |gil| StreamMessage::from_nats_message(gil, message))?;
            Ok(result)
        })
    }
}

#[pyo3::pymodule(submodule, name = "stream")]
pub mod pymod {
    #[pymodule_export]
    pub use super::{
        Compression, ConsumerLimits, DiscardPolicy, External, PersistenceMode, Placement,
        Republish, RetentionPolicy, Source, StorageType, Stream, StreamConfig, StreamMessage,
        SubjectTransform,
    };
}
