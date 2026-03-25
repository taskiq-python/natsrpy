use std::{collections::HashMap, time::Duration};

use crate::{
    exceptions::rust_err::NatsrpyError,
    js::consumers::common::{AckPolicy, DeliverPolicy, ReplayPolicy},
    utils::py_types::TimeValue,
};

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Clone, Debug)]
pub struct PushConsumerConfig {
    pub deliver_subject: String,
    pub name: Option<String>,
    pub durable_name: Option<String>,
    pub description: Option<String>,
    pub deliver_group: Option<String>,
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
    pub flow_control: bool,
    pub idle_heartbeat: Duration,
    pub num_replicas: usize,
    pub memory_storage: bool,
    pub metadata: HashMap<String, String>,
    pub backoff: Vec<Duration>,
    pub inactive_threshold: Duration,
    pub pause_until: Option<i64>,
}

#[pyo3::pymethods]
impl PushConsumerConfig {
    #[new]
    #[pyo3(signature=(
        deliver_subject,
        name=None,
        durable_name=None,
        description=None,
        deliver_group=None,
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
        flow_control=None,
        idle_heartbeat=None,
        num_replicas=None,
        memory_storage=None,
        metadata=None,
        backoff=None,
        inactive_threshold=None,
        pause_until=None,

    ))]
    #[must_use]
    pub fn __new__(
        deliver_subject: String,
        name: Option<String>,
        durable_name: Option<String>,
        description: Option<String>,
        deliver_group: Option<String>,
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
        flow_control: Option<bool>,
        idle_heartbeat: Option<TimeValue>,
        num_replicas: Option<usize>,
        memory_storage: Option<bool>,
        metadata: Option<HashMap<String, String>>,
        backoff: Option<Vec<TimeValue>>,
        inactive_threshold: Option<TimeValue>,
        pause_until: Option<i64>,
    ) -> Self {
        Self {
            deliver_subject,
            durable_name,
            name,
            description,
            deliver_group,
            delivery_start_sequence,
            delivery_start_time,
            pause_until,

            deliver_policy: deliver_policy.unwrap_or_default(),
            ack_policy: ack_policy.unwrap_or_default(),
            ack_wait: ack_wait.unwrap_or_default().into(),
            max_deliver: max_deliver.unwrap_or_default(),
            filter_subject: filter_subject.unwrap_or_default(),
            filter_subjects: filter_subjects.unwrap_or_default(),
            replay_policy: replay_policy.unwrap_or_default(),
            rate_limit: rate_limit.unwrap_or_default(),
            sample_frequency: sample_frequency.unwrap_or_default(),
            max_waiting: max_waiting.unwrap_or_default(),
            max_ack_pending: max_ack_pending.unwrap_or_default(),
            headers_only: headers_only.unwrap_or_default(),
            flow_control: flow_control.unwrap_or_default(),
            idle_heartbeat: idle_heartbeat.unwrap_or_default().into(),
            num_replicas: num_replicas.unwrap_or_default(),
            memory_storage: memory_storage.unwrap_or_default(),
            metadata: metadata.unwrap_or_default(),
            backoff: backoff
                .unwrap_or_default()
                .into_iter()
                .map(Into::into)
                .collect(),
            inactive_threshold: inactive_threshold.unwrap_or_default().into(),
        }
    }
}

impl TryFrom<PushConsumerConfig> for async_nats::jetstream::consumer::push::Config {
    type Error = NatsrpyError;

    fn try_from(value: PushConsumerConfig) -> Result<Self, Self::Error> {
        Ok(Self {
            deliver_subject: value.deliver_subject,
            durable_name: value.durable_name,
            name: value.name,
            description: value.description,
            deliver_group: value.deliver_group,
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
            flow_control: value.flow_control,
            idle_heartbeat: value.idle_heartbeat,
            num_replicas: value.num_replicas,
            memory_storage: value.memory_storage,
            metadata: value.metadata,
            backoff: value.backoff,
            inactive_threshold: value.inactive_threshold,
            pause_until: value
                .pause_until
                .map(time::OffsetDateTime::from_unix_timestamp)
                .transpose()?,
        })
    }
}
