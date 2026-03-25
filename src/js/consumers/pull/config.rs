use std::{collections::HashMap, time::Duration};

use crate::{
    exceptions::rust_err::NatsrpyError,
    js::consumers::common::{AckPolicy, DeliverPolicy, PriorityPolicy, ReplayPolicy},
    utils::py_types::TimeValue,
};

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Clone, Debug, Default)]
pub struct PullConsumerConfig {
    pub name: Option<String>,
    pub durable_name: Option<String>,
    pub description: Option<String>,
    pub deliver_policy: DeliverPolicy,
    pub delivery_start_sequence: Option<u64>,
    pub delivery_start_time: Option<i64>,
    pub ack_policy: AckPolicy,
    pub ack_wait: Duration,
    pub max_deliver: i64,
    pub filter_subject: String,
    pub filter_subjects: Vec<String>,
    pub replay_policy: ReplayPolicy,
    pub rate_limit: u64,
    pub sample_frequency: u8,
    pub max_waiting: i64,
    pub max_ack_pending: i64,
    pub headers_only: bool,
    pub max_batch: i64,
    pub max_bytes: i64,
    pub max_expires: Duration,
    pub inactive_threshold: Duration,
    pub num_replicas: usize,
    pub memory_storage: bool,
    pub metadata: HashMap<String, String>,
    pub backoff: Vec<Duration>,
    pub priority_policy: PriorityPolicy,
    pub priority_groups: Vec<String>,
    pub pause_until: Option<i64>,
}

#[pyo3::pymethods]
impl PullConsumerConfig {
    #[new]
    #[pyo3(signature=(
        name=None,
        durable_name=None,
        description=None,
        deliver_policy=None,
        delivery_start_sequence=None,
        delivery_start_time=None,
        ack_policy=None,
        ack_wait=None,
        max_deliver=None,
        filter_subject=None,
        filter_subjects=None,
        replay_policy=None,
        rate_limit=None,
        sample_frequency=None,
        max_waiting=None,
        max_ack_pending=None,
        headers_only=None,
        max_batch=None,
        max_bytes=None,
        max_expires=None,
        inactive_threshold=None,
        num_replicas=None,
        memory_storage=None,
        metadata=None,
        backoff=None,
        priority_policy=None,
        priority_groups=None,
        pause_until=None,
    ))]
    #[must_use]
    pub fn __new__(
        name: Option<String>,
        durable_name: Option<String>,
        description: Option<String>,
        deliver_policy: Option<DeliverPolicy>,
        delivery_start_sequence: Option<u64>,
        delivery_start_time: Option<i64>,
        ack_policy: Option<AckPolicy>,
        ack_wait: Option<TimeValue>,
        max_deliver: Option<i64>,
        filter_subject: Option<String>,
        filter_subjects: Option<Vec<String>>,
        replay_policy: Option<ReplayPolicy>,
        rate_limit: Option<u64>,
        sample_frequency: Option<u8>,
        max_waiting: Option<i64>,
        max_ack_pending: Option<i64>,
        headers_only: Option<bool>,
        max_batch: Option<i64>,
        max_bytes: Option<i64>,
        max_expires: Option<TimeValue>,
        inactive_threshold: Option<TimeValue>,
        num_replicas: Option<usize>,
        memory_storage: Option<bool>,
        metadata: Option<HashMap<String, String>>,
        backoff: Option<Vec<TimeValue>>,
        priority_policy: Option<PriorityPolicy>,
        priority_groups: Option<Vec<String>>,
        pause_until: Option<i64>,
    ) -> Self {
        let mut conf = Self {
            name,
            durable_name,
            description,
            delivery_start_sequence,
            delivery_start_time,
            pause_until,
            ..Default::default()
        };

        conf.deliver_policy = deliver_policy.unwrap_or_default();
        conf.ack_policy = ack_policy.unwrap_or_default();
        conf.ack_wait = ack_wait.unwrap_or_default().into();
        conf.max_deliver = max_deliver.unwrap_or_default();
        conf.filter_subject = filter_subject.unwrap_or_default();
        conf.filter_subjects = filter_subjects.unwrap_or_default();
        conf.replay_policy = replay_policy.unwrap_or_default();
        conf.rate_limit = rate_limit.unwrap_or_default();
        conf.sample_frequency = sample_frequency.unwrap_or_default();
        conf.max_waiting = max_waiting.unwrap_or_default();
        conf.max_ack_pending = max_ack_pending.unwrap_or_default();
        conf.headers_only = headers_only.unwrap_or_default();
        conf.max_batch = max_batch.unwrap_or_default();
        conf.max_bytes = max_bytes.unwrap_or_default();
        conf.max_expires = max_expires.unwrap_or_default().into();
        conf.inactive_threshold = inactive_threshold.unwrap_or_default().into();
        conf.num_replicas = num_replicas.unwrap_or_default();
        conf.memory_storage = memory_storage.unwrap_or_default();
        conf.metadata = metadata.unwrap_or_default();
        conf.backoff = backoff
            .unwrap_or_default()
            .into_iter()
            .map(Into::into)
            .collect();
        conf.priority_policy = priority_policy.unwrap_or_default();
        conf.priority_groups = priority_groups.unwrap_or_default();

        conf
    }
}

impl TryFrom<PullConsumerConfig> for async_nats::jetstream::consumer::pull::Config {
    type Error = NatsrpyError;

    fn try_from(value: PullConsumerConfig) -> Result<Self, Self::Error> {
        Ok(Self {
            durable_name: value.durable_name,
            name: value.name,
            description: value.description,
            deliver_policy: value.deliver_policy.to_nats_delivery_policy(
                value.delivery_start_sequence,
                value.delivery_start_time,
            )?,
            ack_policy: value.ack_policy.into(),
            ack_wait: value.ack_wait,
            max_deliver: value.max_deliver,
            filter_subject: value.filter_subject,
            filter_subjects: value.filter_subjects,
            replay_policy: value.replay_policy.into(),
            rate_limit: value.rate_limit,
            sample_frequency: value.sample_frequency,
            max_waiting: value.max_waiting,
            max_ack_pending: value.max_ack_pending,
            headers_only: value.headers_only,
            max_batch: value.max_batch,
            max_bytes: value.max_bytes,
            max_expires: value.max_expires,
            inactive_threshold: value.inactive_threshold,
            num_replicas: value.num_replicas,
            memory_storage: value.memory_storage,
            metadata: value.metadata,
            backoff: value.backoff,
            priority_policy: value.priority_policy.into(),
            priority_groups: value.priority_groups,
            pause_until: value
                .pause_until
                .map(time::OffsetDateTime::from_unix_timestamp)
                .transpose()?,
        })
    }
}
