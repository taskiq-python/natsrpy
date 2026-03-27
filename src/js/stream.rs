use pyo3::{
    Py,
    types::{PyBytes, PyDateTime, PyDict},
};
use std::{collections::HashMap, ops::Deref, sync::Arc, time::Duration};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::managers::consumers::ConsumersManager,
    utils::{
        futures::natsrpy_future_with_timeout,
        headers::NatsrpyHeadermapExt,
        py_types::{TimeValue, ToPyDate},
    },
};
use pyo3::{Bound, PyAny, Python};

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
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

impl From<async_nats::jetstream::stream::StorageType> for StorageType {
    fn from(value: async_nats::jetstream::stream::StorageType) -> Self {
        match value {
            async_nats::jetstream::stream::StorageType::File => Self::FILE,
            async_nats::jetstream::stream::StorageType::Memory => Self::MEMORY,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
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

impl From<async_nats::jetstream::stream::DiscardPolicy> for DiscardPolicy {
    fn from(value: async_nats::jetstream::stream::DiscardPolicy) -> Self {
        match value {
            async_nats::jetstream::stream::DiscardPolicy::Old => Self::OLD,
            async_nats::jetstream::stream::DiscardPolicy::New => Self::NEW,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
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

impl From<async_nats::jetstream::stream::RetentionPolicy> for RetentionPolicy {
    fn from(value: async_nats::jetstream::stream::RetentionPolicy) -> Self {
        match value {
            async_nats::jetstream::stream::RetentionPolicy::Limits => Self::LIMITS,
            async_nats::jetstream::stream::RetentionPolicy::Interest => Self::INTEREST,
            async_nats::jetstream::stream::RetentionPolicy::WorkQueue => Self::WORKQUEUE,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Compression {
    #[default]
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

impl From<async_nats::jetstream::stream::Compression> for Compression {
    fn from(value: async_nats::jetstream::stream::Compression) -> Self {
        match value {
            async_nats::jetstream::stream::Compression::S2 => Self::S2,
            async_nats::jetstream::stream::Compression::None => Self::NONE,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
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

impl From<async_nats::jetstream::stream::PersistenceMode> for PersistenceMode {
    fn from(value: async_nats::jetstream::stream::PersistenceMode) -> Self {
        match value {
            async_nats::jetstream::stream::PersistenceMode::Default => Self::Default,
            async_nats::jetstream::stream::PersistenceMode::Async => Self::Async,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct ConsumerLimits {
    pub inactive_threshold: Duration,
    pub max_ack_pending: i64,
}

#[pyo3::pymethods]
impl ConsumerLimits {
    #[new]
    #[must_use]
    pub fn __new__(inactive_threshold: TimeValue, max_ack_pending: i64) -> Self {
        Self {
            inactive_threshold: inactive_threshold.into(),
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

impl From<async_nats::jetstream::stream::ConsumerLimits> for ConsumerLimits {
    fn from(value: async_nats::jetstream::stream::ConsumerLimits) -> Self {
        Self {
            inactive_threshold: value.inactive_threshold,
            max_ack_pending: value.max_ack_pending,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone)]
pub struct Republish {
    pub source: String,
    pub destination: String,
    pub headers_only: bool,
}

#[pyo3::pymethods]
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

impl From<async_nats::jetstream::stream::Republish> for Republish {
    fn from(value: async_nats::jetstream::stream::Republish) -> Self {
        Self {
            source: value.source,
            destination: value.destination,
            headers_only: value.headers_only,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone)]
pub struct External {
    pub api_prefix: String,
    pub delivery_prefix: Option<String>,
}

#[pyo3::pymethods]
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

impl From<async_nats::jetstream::stream::External> for External {
    fn from(value: async_nats::jetstream::stream::External) -> Self {
        Self {
            api_prefix: value.api_prefix,
            delivery_prefix: value.delivery_prefix,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone)]
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

impl From<async_nats::jetstream::stream::SubjectTransform> for SubjectTransform {
    fn from(value: async_nats::jetstream::stream::SubjectTransform) -> Self {
        Self {
            source: value.source,
            destination: value.destination,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone)]
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

impl From<async_nats::jetstream::stream::Source> for Source {
    fn from(value: async_nats::jetstream::stream::Source) -> Self {
        Self {
            name: value.name,
            filter_subject: value.filter_subject,
            external: value.external.map(std::convert::Into::into),
            start_sequence: value.start_sequence,
            start_time: value.start_time.map(time::OffsetDateTime::unix_timestamp),
            domain: value.domain,
            subject_transforms: value
                .subject_transforms
                .into_iter()
                .map(Into::into)
                .collect(),
        }
    }
}

#[pyo3::pymethods]
impl Source {
    #[new]
    #[pyo3(signature = (
        name,
        filter_subject=None,
        external=None,
        start_sequence = None,
        start_time=None,
        domain=None,
        subject_transforms = None
    ))]
    pub fn __new__(
        name: String,
        filter_subject: Option<String>,
        external: Option<Bound<'_, External>>,
        start_sequence: Option<u64>,
        start_time: Option<i64>,
        domain: Option<String>,
        subject_transforms: Option<Vec<Bound<'_, SubjectTransform>>>,
    ) -> NatsrpyResult<Self> {
        Ok(Self {
            name,
            domain,
            start_time,
            start_sequence,
            filter_subject,
            subject_transforms: subject_transforms
                .unwrap_or_default()
                .into_iter()
                .map(|val| val.borrow().deref().clone())
                .collect(),
            external: external.map(|e| e.borrow().deref().clone()),
        })
    }
}

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone)]
pub struct Placement {
    pub cluster: Option<String>,
    pub tags: Vec<String>,
}

#[pyo3::pymethods]
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

impl From<async_nats::jetstream::stream::Placement> for Placement {
    fn from(value: async_nats::jetstream::stream::Placement) -> Self {
        Self {
            cluster: value.cluster,
            tags: value.tags,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct PeerInfo {
    pub name: String,
    pub current: bool,
    pub active: Duration,
    pub offline: bool,
    pub lag: Option<u64>,
}

impl From<PeerInfo> for async_nats::jetstream::stream::PeerInfo {
    fn from(value: PeerInfo) -> Self {
        Self {
            name: value.name,
            current: value.current,
            active: value.active,
            offline: value.offline,
            lag: value.lag,
        }
    }
}

impl From<async_nats::jetstream::stream::PeerInfo> for PeerInfo {
    fn from(value: async_nats::jetstream::stream::PeerInfo) -> Self {
        Self {
            name: value.name,
            current: value.current,
            active: value.active,
            offline: value.offline,
            lag: value.lag,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct ClusterInfo {
    pub name: Option<String>,
    pub raft_group: Option<String>,
    pub leader: Option<String>,
    pub leader_since: Option<i64>,
    pub system_account: bool,
    pub traffic_account: Option<String>,
    pub replicas: Vec<PeerInfo>,
}

impl TryFrom<ClusterInfo> for async_nats::jetstream::stream::ClusterInfo {
    type Error = NatsrpyError;
    fn try_from(value: ClusterInfo) -> Result<Self, Self::Error> {
        Ok(Self {
            name: value.name,
            raft_group: value.raft_group,
            leader: value.leader,
            leader_since: value
                .leader_since
                .map(time::OffsetDateTime::from_unix_timestamp)
                .transpose()?,
            system_account: value.system_account,
            traffic_account: value.traffic_account,
            replicas: value.replicas.into_iter().map(Into::into).collect(),
        })
    }
}

impl From<async_nats::jetstream::stream::ClusterInfo> for ClusterInfo {
    fn from(value: async_nats::jetstream::stream::ClusterInfo) -> Self {
        Self {
            name: value.name,
            raft_group: value.raft_group,
            leader: value.leader,
            leader_since: value.leader_since.map(time::OffsetDateTime::unix_timestamp),
            system_account: value.system_account,
            traffic_account: value.traffic_account,
            replicas: value.replicas.into_iter().map(Into::into).collect(),
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone, Default)]
#[allow(clippy::struct_excessive_bools)]
pub struct StreamConfig {
    pub name: String,
    pub subjects: Vec<String>,
    pub max_bytes: i64,
    pub max_messages: i64,
    pub max_messages_per_subject: i64,
    pub discard: DiscardPolicy,
    pub discard_new_per_subject: bool,
    pub retention: RetentionPolicy,
    pub max_consumers: i32,
    pub max_age: Duration,
    pub max_message_size: i32,
    pub storage: StorageType,
    pub num_replicas: usize,
    pub no_ack: bool,
    pub duplicate_window: Duration,
    pub template_owner: String,
    pub sealed: bool,
    pub description: Option<String>,
    pub allow_rollup: bool,
    pub deny_delete: bool,
    pub deny_purge: bool,
    pub republish: Option<Republish>,
    pub allow_direct: bool,
    pub mirror_direct: bool,
    pub mirror: Option<Source>,
    pub sources: Option<Vec<Source>>,
    pub metadata: HashMap<String, String>,
    pub subject_transform: Option<SubjectTransform>,
    pub compression: Option<Compression>,
    pub consumer_limits: Option<ConsumerLimits>,
    pub first_sequence: Option<u64>,
    pub placement: Option<Placement>,
    pub persist_mode: Option<PersistenceMode>,
    pub pause_until: Option<i64>,
    pub allow_message_ttl: bool,
    pub subject_delete_marker_ttl: Option<Duration>,
    pub allow_atomic_publish: bool,
    pub allow_message_schedules: bool,
    pub allow_message_counter: bool,
}

#[pyo3::pymethods]
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
    pub fn __new__(
        name: String,
        subjects: Vec<String>,
        max_bytes: Option<i64>,
        max_messages: Option<i64>,
        max_messages_per_subject: Option<i64>,
        discard: Option<DiscardPolicy>,
        discard_new_per_subject: Option<bool>,
        retention: Option<RetentionPolicy>,
        max_consumers: Option<i32>,
        max_age: Option<TimeValue>,
        max_message_size: Option<i32>,
        storage: Option<StorageType>,
        num_replicas: Option<usize>,
        no_ack: Option<bool>,
        duplicate_window: Option<TimeValue>,
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
        subject_delete_marker_ttl: Option<TimeValue>,
        allow_atomic_publish: Option<bool>,
        allow_message_schedules: Option<bool>,
        allow_message_counter: Option<bool>,
    ) -> NatsrpyResult<Self> {
        let config = Self {
            name,
            subjects,
            description,
            republish,
            mirror,
            sources,
            subject_transform,
            compression,
            consumer_limits,
            first_sequence,
            placement,
            persist_mode,
            pause_until,

            subject_delete_marker_ttl: subject_delete_marker_ttl.map(Into::into),
            max_bytes: max_bytes.unwrap_or_default(),
            max_messages: max_messages.unwrap_or_default(),
            max_messages_per_subject: max_messages_per_subject.unwrap_or_default(),
            discard: discard.unwrap_or_default(),
            discard_new_per_subject: discard_new_per_subject.unwrap_or_default(),
            retention: retention.unwrap_or_default(),
            max_consumers: max_consumers.unwrap_or_default(),
            max_age: max_age.unwrap_or_default().into(),
            max_message_size: max_message_size.unwrap_or_default(),
            storage: storage.unwrap_or_default(),
            num_replicas: num_replicas.unwrap_or_default(),
            no_ack: no_ack.unwrap_or_default(),
            duplicate_window: duplicate_window.unwrap_or_default().into(),
            template_owner: template_owner.unwrap_or_default(),
            sealed: sealed.unwrap_or_default(),
            allow_rollup: allow_rollup.unwrap_or_default(),
            deny_delete: deny_delete.unwrap_or_default(),
            deny_purge: deny_purge.unwrap_or_default(),
            allow_direct: allow_direct.unwrap_or_default(),
            mirror_direct: mirror_direct.unwrap_or_default(),
            metadata: metadata.unwrap_or_default(),
            allow_message_ttl: allow_message_ttl.unwrap_or_default(),
            allow_atomic_publish: allow_atomic_publish.unwrap_or_default(),
            allow_message_schedules: allow_message_schedules.unwrap_or_default(),
            allow_message_counter: allow_message_counter.unwrap_or_default(),
        };

        Ok(config)
    }
}

impl TryFrom<async_nats::jetstream::stream::Config> for StreamConfig {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::jetstream::stream::Config) -> Result<Self, Self::Error> {
        Ok(Self {
            name: value.name,
            subjects: value.subjects,
            max_bytes: value.max_bytes,
            max_messages: value.max_messages,
            max_messages_per_subject: value.max_messages_per_subject,
            discard: value.discard.into(),
            discard_new_per_subject: value.discard_new_per_subject,
            retention: value.retention.into(),
            max_consumers: value.max_consumers,
            max_age: value.max_age,
            max_message_size: value.max_message_size,
            storage: value.storage.into(),
            num_replicas: value.num_replicas,
            no_ack: value.no_ack,
            duplicate_window: value.duplicate_window,
            template_owner: value.template_owner,
            sealed: value.sealed,
            description: value.description,
            allow_rollup: value.allow_rollup,
            deny_delete: value.deny_delete,
            deny_purge: value.deny_purge,
            republish: value.republish.map(Into::into),
            allow_direct: value.allow_direct,
            mirror_direct: value.mirror_direct,
            mirror: value.mirror.map(Into::into),
            sources: value
                .sources
                .map(|val| val.into_iter().map(Into::into).collect()),
            metadata: value.metadata,
            subject_transform: value.subject_transform.map(Into::into),
            compression: value.compression.map(Into::into),
            consumer_limits: value.consumer_limits.map(Into::into),
            first_sequence: value.first_sequence,
            placement: value.placement.map(Into::into),
            persist_mode: value.persist_mode.map(Into::into),
            pause_until: value.pause_until.map(time::OffsetDateTime::unix_timestamp),
            allow_message_ttl: value.allow_message_ttl,
            subject_delete_marker_ttl: value.subject_delete_marker_ttl,
            allow_atomic_publish: value.allow_atomic_publish,
            allow_message_schedules: value.allow_message_schedules,
            allow_message_counter: value.allow_message_counter,
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
        conf.max_bytes = value.max_bytes;
        conf.max_messages = value.max_messages;
        conf.max_messages_per_subject = value.max_messages_per_subject;
        conf.discard_new_per_subject = value.discard_new_per_subject;
        conf.max_consumers = value.max_consumers;
        conf.max_age = value.max_age;
        conf.max_message_size = value.max_message_size;
        conf.num_replicas = value.num_replicas;
        conf.no_ack = value.no_ack;
        conf.duplicate_window = value.duplicate_window;
        conf.template_owner = value.template_owner;
        conf.sealed = value.sealed;
        conf.allow_rollup = value.allow_rollup;
        conf.deny_delete = value.deny_delete;
        conf.deny_purge = value.deny_purge;
        conf.allow_direct = value.allow_direct;
        conf.mirror_direct = value.mirror_direct;
        conf.metadata = value.metadata;
        conf.allow_message_ttl = value.allow_message_ttl;
        conf.allow_atomic_publish = value.allow_atomic_publish;
        conf.allow_message_schedules = value.allow_message_schedules;
        conf.allow_message_counter = value.allow_message_counter;

        // Values that require conversion between python -> rust types.
        conf.republish = value.republish.map(Into::into);
        conf.storage = value.storage.into();
        conf.retention = value.retention.into();
        conf.discard = value.discard.into();
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

#[pyo3::pyclass(get_all)]
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
        msg: &async_nats::jetstream::message::StreamMessage,
    ) -> NatsrpyResult<Self> {
        Ok(Self {
            subject: msg.subject.to_string(),
            payload: PyBytes::new(py, &msg.payload).unbind(),
            headers: msg.headers.to_pydict(py)?.unbind(),
            sequence: msg.sequence,
            time: msg.time.to_py_date(py)?.unbind(),
        })
    }
}

#[pyo3::pymethods]
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

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct StreamState {
    pub messages: u64,
    pub bytes: u64,
    pub first_sequence: u64,
    pub first_timestamp: i64,
    pub last_sequence: u64,
    pub last_timestamp: i64,
    pub consumer_count: usize,
    pub subjects_count: u64,
    pub deleted_count: Option<u64>,
    pub deleted: Option<Vec<u64>>,
}

impl From<async_nats::jetstream::stream::State> for StreamState {
    fn from(value: async_nats::jetstream::stream::State) -> Self {
        Self {
            messages: value.messages,
            bytes: value.bytes,
            first_sequence: value.first_sequence,
            first_timestamp: value.first_timestamp.unix_timestamp(),
            last_sequence: value.last_sequence,
            last_timestamp: value.last_timestamp.unix_timestamp(),
            consumer_count: value.consumer_count,
            subjects_count: value.subjects_count,
            deleted_count: value.deleted_count,
            deleted: value.deleted,
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct SourceInfo {
    pub name: String,
    pub lag: u64,
    pub active: Option<std::time::Duration>,
    pub filter_subject: Option<String>,
    pub subject_transform_dest: Option<String>,
    pub subject_transforms: Vec<SubjectTransform>,
}

impl From<async_nats::jetstream::stream::SourceInfo> for SourceInfo {
    fn from(value: async_nats::jetstream::stream::SourceInfo) -> Self {
        Self {
            name: value.name,
            lag: value.lag,
            active: value.active,
            filter_subject: value.filter_subject,
            subject_transform_dest: value.subject_transform_dest,
            subject_transforms: value
                .subject_transforms
                .into_iter()
                .map(Into::into)
                .collect(),
        }
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Debug, Clone)]
pub struct StreamInfo {
    pub config: StreamConfig,
    pub created: i64,
    pub state: StreamState,
    pub cluster: Option<ClusterInfo>,
    pub mirror: Option<SourceInfo>,
    pub sources: Vec<SourceInfo>,
}

#[pyo3::pymethods]
impl StreamInfo {
    #[must_use]
    pub fn __str__(&self) -> String {
        format!("{self:#?}")
    }
}

impl TryFrom<async_nats::jetstream::stream::Info> for StreamInfo {
    type Error = NatsrpyError;
    fn try_from(value: async_nats::jetstream::stream::Info) -> Result<Self, Self::Error> {
        Ok(Self {
            config: value.config.try_into()?,
            created: value.created.unix_timestamp(),
            state: value.state.into(),
            cluster: value.cluster.map(Into::into),
            mirror: value.mirror.map(Into::into),
            sources: value.sources.into_iter().map(Into::into).collect(),
        })
    }
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Clone, Debug)]
pub struct PurgeResponse {
    success: bool,
    purged: u64,
}

impl From<async_nats::jetstream::stream::PurgeResponse> for PurgeResponse {
    fn from(value: async_nats::jetstream::stream::PurgeResponse) -> Self {
        Self {
            success: value.success,
            purged: value.purged,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct Stream {
    #[pyo3(get)]
    name: String,
    stream: Arc<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
}
impl Stream {
    #[must_use]
    pub fn new(
        stream: async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>,
    ) -> Self {
        let info = stream.cached_info();
        Self {
            name: info.config.name.clone(),
            stream: Arc::new(stream),
        }
    }
}

#[pyo3::pymethods]
impl Stream {
    #[getter]
    #[must_use]
    pub fn consumers(&self) -> ConsumersManager {
        ConsumersManager::new(self.stream.clone())
    }

    #[pyo3(signature=(sequence, timeout=None))]
    pub fn direct_get<'py>(
        &self,
        py: Python<'py>,
        sequence: u64,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let message = ctx.direct_get(sequence).await?;
            let result =
                Python::attach(move |gil| StreamMessage::from_nats_message(gil, &message))?;
            Ok(result)
        })
    }

    #[pyo3(signature=(subject, sequence=None, timeout=None))]
    pub fn direct_get_next_for_subject<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        sequence: Option<u64>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let message = ctx.direct_get_next_for_subject(subject, sequence).await?;
            let result =
                Python::attach(move |gil| StreamMessage::from_nats_message(gil, &message))?;
            Ok(result)
        })
    }

    #[pyo3(signature=(subject, timeout=None))]
    pub fn direct_get_first_for_subject<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let message = ctx.direct_get_first_for_subject(subject).await?;
            let result =
                Python::attach(move |gil| StreamMessage::from_nats_message(gil, &message))?;
            Ok(result)
        })
    }

    #[pyo3(signature=(subject, timeout=None))]
    pub fn direct_get_last_for_subject<'py>(
        &self,
        py: Python<'py>,
        subject: String,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let message = ctx.direct_get_last_for_subject(subject).await?;
            let result =
                Python::attach(move |gil| StreamMessage::from_nats_message(gil, &message))?;
            Ok(result)
        })
    }

    #[pyo3(signature=(timeout=None))]
    pub fn get_info<'py>(
        &self,
        py: Python<'py>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            StreamInfo::try_from(ctx.get_info().await?)
        })
    }

    #[pyo3(signature=(
        filter=None,
        sequence=None,
        keep=None,
        timeout=None,
    ))]
    pub fn purge<'py>(
        &self,
        py: Python<'py>,
        filter: Option<String>,
        sequence: Option<u64>,
        keep: Option<u64>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let mut purge_request = ctx.purge();
            if let Some(filter) = filter {
                purge_request = purge_request.filter(filter);
            }
            let purge_response = match (sequence, keep) {
                (None, None) => purge_request.await,
                (Some(seq), None) => purge_request.sequence(seq).await,
                (None, Some(keep)) => purge_request.keep(keep).await,
                _ => {
                    return Err(NatsrpyError::InvalidArgument(String::from(
                        "Either keep or sequence can be set, but not both.",
                    )));
                }
            };
            let resp = purge_response?;
            if !resp.success {
                return Err(NatsrpyError::SessionError(String::from(
                    "Purge failed. Check server logs for more info.",
                )));
            }
            Ok(resp.purged)
        })
    }

    #[pyo3(signature=(sequence, timeout=None))]
    pub fn delete_message<'py>(
        &self,
        py: Python<'py>,
        sequence: u64,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            ctx.delete_message(sequence).await?;
            Ok(())
        })
    }

    #[must_use]
    pub fn __repr__(&self) -> String {
        format!("Stream<name={name:?}>", name = self.name)
    }
}

#[pyo3::pymodule(submodule, name = "stream")]
pub mod pymod {
    #[pymodule_export]
    pub use super::{
        ClusterInfo, Compression, ConsumerLimits, DiscardPolicy, External, PeerInfo,
        PersistenceMode, Placement, Republish, RetentionPolicy, Source, SourceInfo, StorageType,
        Stream, StreamConfig, StreamInfo, StreamMessage, StreamState, SubjectTransform,
    };
}
