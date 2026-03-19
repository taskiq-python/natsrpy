use crate::exceptions::rust_err::{NatsrpyError, NatsrpyResult};

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum DeliverPolicy {
    #[default]
    All,
    Last,
    New,
    ByStartSequence,
    ByStartTime,
    LastPerSubject,
}

impl DeliverPolicy {
    pub fn to_nats_delivery_policy(
        &self,
        start_sequence: Option<u64>,
        start_time: Option<i64>,
    ) -> NatsrpyResult<async_nats::jetstream::consumer::DeliverPolicy> {
        let result = match self {
            Self::All => async_nats::jetstream::consumer::DeliverPolicy::All,
            Self::Last => async_nats::jetstream::consumer::DeliverPolicy::Last,
            Self::New => async_nats::jetstream::consumer::DeliverPolicy::New,
            Self::LastPerSubject => async_nats::jetstream::consumer::DeliverPolicy::Last,
            Self::ByStartSequence => {
                let Some(start_sequence) = start_sequence else {
                    return Err(NatsrpyError::SessionError(String::from(
                        "Start sequence is not present",
                    )));
                };
                async_nats::jetstream::consumer::DeliverPolicy::ByStartSequence { start_sequence }
            }
            Self::ByStartTime => {
                let Some(start_time) = start_time else {
                    return Err(NatsrpyError::SessionError(String::from(
                        "Start sequence is not present",
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
    Explicit,
    None,
    All,
}

impl From<AckPolicy> for async_nats::jetstream::consumer::AckPolicy {
    fn from(value: AckPolicy) -> Self {
        match value {
            AckPolicy::Explicit => Self::Explicit,
            AckPolicy::None => Self::None,
            AckPolicy::All => Self::All,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum ReplayPolicy {
    #[default]
    Instant,
    Original,
}

impl From<ReplayPolicy> for async_nats::jetstream::consumer::ReplayPolicy {
    fn from(value: ReplayPolicy) -> Self {
        match value {
            ReplayPolicy::Instant => Self::Instant,
            ReplayPolicy::Original => Self::Original,
        }
    }
}

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone, Default, Copy, PartialEq, Eq, PartialOrd)]
pub enum PriorityPolicy {
    #[default]
    None,
    Overflow,
    PinnedClient,
    Prioritized,
}

impl From<PriorityPolicy> for async_nats::jetstream::consumer::PriorityPolicy {
    fn from(value: PriorityPolicy) -> Self {
        match value {
            PriorityPolicy::None => Self::None,
            PriorityPolicy::Overflow => Self::Overflow,
            PriorityPolicy::PinnedClient => Self::PinnedClient,
            PriorityPolicy::Prioritized => Self::Prioritized,
        }
    }
}
