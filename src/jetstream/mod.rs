pub mod jetstream;
pub mod kv;

pub use jetstream::JetStream;

use pyo3::pymodule;

#[pymodule(name = "jetstream")]
pub mod pymod {
    #[pymodule_export]
    use super::jetstream::JetStream;

    #[pymodule_export]
    use super::jetstream::StorageType;
}
