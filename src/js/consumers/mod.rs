pub mod common;
pub mod pull;
pub mod push;

#[pyo3::pymodule(submodule, name = "consumers")]
pub mod pymod {
    #[pymodule_export]
    use super::common::{AckPolicy, DeliverPolicy, PriorityPolicy, ReplayPolicy};
    #[pymodule_export]
    pub use super::pull::{config::PullConsumerConfig, consumer::PullConsumer};
    #[pymodule_export]
    pub use super::push::{
        config::PushConsumerConfig, consumer::MessagesIterator, consumer::PushConsumer,
    };
}
