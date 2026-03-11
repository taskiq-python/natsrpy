pub mod jetstream;
pub mod kv;
pub mod stream;

#[pyo3::pymodule(submodule, name = "js")]
pub mod pymod {
    #[pymodule_export]
    pub use super::jetstream::JetStream;
    #[pymodule_export]
    pub use super::kv::KVConfig;

    #[pymodule_export]
    pub use super::kv::KeyValue;

    #[pymodule_export]
    pub use super::kv::pymod as kv;
    #[pymodule_export]
    pub use super::stream::pymod as stream;
}
