pub mod consumers;
pub mod jetstream;
pub mod kv;
pub mod stream;

#[pyo3::pymodule(submodule, name = "js")]
pub mod pymod {
    // Classes
    #[pymodule_export]
    pub use super::{
        consumers::{pull::PullConsumer, push::PushConsumer},
        jetstream::JetStream,
        kv::{KVConfig, KeyValue},
    };

    // SubModules
    #[pymodule_export]
    pub use super::kv::pymod as kv;
    #[pymodule_export]
    pub use super::stream::pymod as stream;
}
