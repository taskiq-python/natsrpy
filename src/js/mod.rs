pub mod consumers;
pub mod counters;
pub mod jetstream;
pub mod kv;
pub mod managers;
pub mod message;
pub mod object_store;
pub mod stream;

#[pyo3::pymodule(submodule, name = "js")]
pub mod pymod {
    // Classes
    #[pymodule_export]
    pub use super::jetstream::{JetStream, Publication};

    #[pymodule_export]
    pub use super::message::JetStreamMessage;

    // SubModules
    #[pymodule_export]
    pub use super::consumers::pymod as consumers;
    #[pymodule_export]
    pub use super::counters::pymod as counters;
    #[pymodule_export]
    pub use super::kv::pymod as kv;
    #[pymodule_export]
    pub use super::managers::pymod as managers;
    #[pymodule_export]
    pub use super::object_store::pymod as object_store;
    #[pymodule_export]
    pub use super::stream::pymod as stream;
}
