use std::{collections::HashMap, time::Duration};

use crate::{
    exceptions::rust_err::NatsrpyError,
    js::consumers::common::{AckPolicy, DeliverPolicy, PriorityPolicy, ReplayPolicy},
};

#[pyo3::pyclass(from_py_object, get_all, set_all)]
#[derive(Clone, Debug)]
pub struct PullConsumerConfig {
    pub durable_name: Option<String>,
    pub name: Option<String>,
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

impl PullConsumerConfig {}

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
