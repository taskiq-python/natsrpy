use crate::exceptions::rust_err::{NatsrpyError, NatsrpyResult};

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum DeliverPolicy {
    #[default]
    ALL,
    LAST,
    NEW,
    BY_START_SEQUENCE,
    BY_START_TIME,
    LAST_PER_SUBJECT,
}

impl DeliverPolicy {
    pub fn to_nats_delivery_policy(
        &self,
        start_sequence: Option<u64>,
        start_time: Option<i64>,
    ) -> NatsrpyResult<async_nats::jetstream::consumer::DeliverPolicy> {
        let result = match self {
            Self::ALL => async_nats::jetstream::consumer::DeliverPolicy::All,
            Self::LAST => async_nats::jetstream::consumer::DeliverPolicy::Last,
            Self::NEW => async_nats::jetstream::consumer::DeliverPolicy::New,
            Self::LAST_PER_SUBJECT => {
                async_nats::jetstream::consumer::DeliverPolicy::LastPerSubject
            }
            Self::BY_START_SEQUENCE => {
                let Some(start_sequence) = start_sequence else {
                    return Err(NatsrpyError::SessionError(String::from(
                        "Start sequence is not present, but deliver_policy is set to BY_START_SEQUENCE",
                    )));
                };
                async_nats::jetstream::consumer::DeliverPolicy::ByStartSequence { start_sequence }
            }
            Self::BY_START_TIME => {
                let Some(start_time) = start_time else {
                    return Err(NatsrpyError::SessionError(String::from(
                        "Start time is not present, but deliver_policy is set to BY_START_TIME",
                    )));
                };
                async_nats::jetstream::consumer::DeliverPolicy::ByStartTime {
                    start_time: time::OffsetDateTime::from_unix_timestamp(start_time)?,
                }
            }
        };
        Ok(result)
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum AckPolicy {
    #[default]
    EXPLICIT,
    NONE,
    ALL,
}

impl From<AckPolicy> for async_nats::jetstream::consumer::AckPolicy {
    fn from(value: AckPolicy) -> Self {
        match value {
            AckPolicy::EXPLICIT => Self::Explicit,
            AckPolicy::NONE => Self::None,
            AckPolicy::ALL => Self::All,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum ReplayPolicy {
    #[default]
    INSTANT,
    ORIGINAL,
}

impl From<ReplayPolicy> for async_nats::jetstream::consumer::ReplayPolicy {
    fn from(value: ReplayPolicy) -> Self {
        match value {
            ReplayPolicy::INSTANT => Self::Instant,
            ReplayPolicy::ORIGINAL => Self::Original,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum PriorityPolicy {
    #[default]
    NONE,
    OVERFLOW,
    PINNED_CLIENT,
    PRIORITIZED,
}

impl From<PriorityPolicy> for async_nats::jetstream::consumer::PriorityPolicy {
    fn from(value: PriorityPolicy) -> Self {
        match value {
            PriorityPolicy::NONE => Self::None,
            PriorityPolicy::OVERFLOW => Self::Overflow,
            PriorityPolicy::PINNED_CLIENT => Self::PinnedClient,
            PriorityPolicy::PRIORITIZED => Self::Prioritized,
        }
    }
}
