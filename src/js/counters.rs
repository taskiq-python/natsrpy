use std::{collections::HashMap, sync::Arc, time::Duration};

use async_nats::{HeaderMap, jetstream::context::traits::Publisher};
use pyo3::{Bound, PyAny, Python};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::stream::{
        Compression, ConsumerLimits, DiscardPolicy, PersistenceMode, Placement, Republish,
        RetentionPolicy, Source, StorageType, SubjectTransform,
    },
    utils::{futures::natsrpy_future_with_timeout, py_types::TimeValue},
};

const COUNTER_INCREMENT_HEADER: &str = "Nats-Incr";
const COUNTER_SOURCES_HEADER: &str = "Nats-Counter-Sources";
type CounterSources = HashMap<String, HashMap<String, i128>>;

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Debug, Clone, Default)]
#[allow(clippy::struct_excessive_bools)]
pub struct CountersConfig {
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
}

#[pyo3::pymethods]
impl CountersConfig {
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
    ) -> Self {
        Self {
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
            mirror_direct: mirror_direct.unwrap_or_default(),
            metadata: metadata.unwrap_or_default(),
            allow_message_ttl: allow_message_ttl.unwrap_or_default(),
            allow_atomic_publish: allow_atomic_publish.unwrap_or_default(),
            allow_message_schedules: allow_message_schedules.unwrap_or_default(),
        }
    }
}

impl TryFrom<CountersConfig> for async_nats::jetstream::stream::Config {
    type Error = NatsrpyError;

    fn try_from(value: CountersConfig) -> Result<Self, Self::Error> {
        let mut conf = Self {
            name: value.name,
            subjects: value.subjects,
            description: value.description,
            first_sequence: value.first_sequence,
            subject_delete_marker_ttl: value.subject_delete_marker_ttl,
            allow_direct: true,
            allow_message_counter: true,
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
        conf.mirror_direct = value.mirror_direct;
        conf.metadata = value.metadata;
        conf.allow_message_ttl = value.allow_message_ttl;
        conf.allow_atomic_publish = value.allow_atomic_publish;
        conf.allow_message_schedules = value.allow_message_schedules;

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

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct CounterPayload<'a> {
    val: &'a str,
}

#[pyo3::pyclass(from_py_object, get_all)]
#[derive(Clone)]
pub struct CounterEntry {
    pub subject: String,
    pub value: i128,
    pub sources: CounterSources,
    pub increment: Option<i128>,
}

impl TryFrom<async_nats::jetstream::message::StreamMessage> for CounterEntry {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::jetstream::message::StreamMessage) -> Result<Self, Self::Error> {
        let counter_value = serde_json::from_slice::<CounterPayload>(&value.payload)?
            .val
            .parse::<i128>()?;
        let sources = parse_sources(&value.headers)?;
        let increment = parse_increment(&value.headers)?;
        Ok(Self {
            subject: value.subject.to_string(),
            value: counter_value,
            sources,
            increment,
        })
    }
}

#[pyo3::pymethods]
impl CounterEntry {
    pub fn __repr__(&self) -> String {
        format!(
            "CounterEntry<subject={:?}, value={}, increment={}>",
            self.subject,
            self.value,
            self.increment
                .as_ref()
                .map_or_else(|| String::from("None"), ToString::to_string)
        )
    }
}

#[pyo3::pyclass]
#[allow(dead_code)]
pub struct Counters {
    stream: Arc<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
    js: Arc<async_nats::jetstream::Context>,
}

impl Counters {
    #[must_use]
    pub fn new(
        stream: async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>,
        js: Arc<async_nats::jetstream::Context>,
    ) -> Self {
        Self {
            stream: Arc::new(stream),
            js,
        }
    }
}

fn parse_sources(headers: &HeaderMap) -> NatsrpyResult<CounterSources> {
    let Some(sources) = headers.get(COUNTER_SOURCES_HEADER) else {
        return Ok(CounterSources::new());
    };
    let raw_sources =
        serde_json::from_str::<HashMap<String, HashMap<String, String>>>(sources.as_str())?;
    let mut sources = CounterSources::new();
    for (source_id, subjects) in raw_sources {
        let mut subject_values = HashMap::new();
        for (subject, value_str) in subjects {
            subject_values.insert(subject, value_str.parse()?);
        }
        sources.insert(source_id, subject_values);
    }

    Ok(sources)
}

pub fn parse_increment(headers: &HeaderMap) -> NatsrpyResult<Option<i128>> {
    let Some(header_value) = headers.get(COUNTER_INCREMENT_HEADER) else {
        return Ok(None);
    };
    Ok(Some(header_value.as_str().parse()?))
}

#[pyo3::pymethods]
impl Counters {
    #[pyo3(signature=(key, value, timeout=None))]
    pub fn add<'py>(
        &self,
        py: Python<'py>,
        key: String,
        value: i128,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let js = self.js.clone();
        let mut headers = HeaderMap::new();
        headers.insert(COUNTER_INCREMENT_HEADER, value.to_string());
        natsrpy_future_with_timeout(py, timeout, async move {
            let resp = js
                .publish_message(async_nats::jetstream::message::OutboundMessage {
                    subject: key.into(),
                    payload: bytes::Bytes::new(),
                    headers: Some(headers),
                })
                .await?
                .await?;
            match &resp.value {
                Some(val) => Ok(val.parse::<i128>()?),
                None => Err(NatsrpyError::SessionError(String::from(
                    "Missing counter response value.",
                ))),
            }
        })
    }

    #[pyo3(signature=(key, timeout=None))]
    pub fn incr<'py>(
        &self,
        py: Python<'py>,
        key: String,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.add(py, key, 1, timeout)
    }

    #[pyo3(signature=(key, timeout=None))]
    pub fn decr<'py>(
        &self,
        py: Python<'py>,
        key: String,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.add(py, key, -1, timeout)
    }

    #[pyo3(signature=(key, timeout=None))]
    pub fn get<'py>(
        &self,
        py: Python<'py>,
        key: String,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let stream_guard = self.stream.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let message = stream_guard.direct_get_last_for_subject(key).await?;
            CounterEntry::try_from(message)
        })
    }
}

#[pyo3::pymodule(submodule, name = "counters")]
pub mod pymod {
    #[pymodule_export]
    use super::{CounterEntry, Counters, CountersConfig};
}
