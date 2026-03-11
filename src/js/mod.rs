pub mod jetstream;
pub mod kv;
pub mod stream;

use pyo3::pymodule;

#[pymodule(submodule, name = "js")]
pub mod pymod {

    use pyo3::types::{PyModule, PyModuleMethods};
    use pyo3::{Bound, PyResult};

    #[pymodule_export]
    pub use super::jetstream::JetStream;
    #[pymodule_export]
    pub use super::kv::KVConfig;
    #[pymodule_export]
    pub use super::stream::{
        External, Placement, Republish, Source, StorageType, SubjectTransform,
    };

    #[pymodule_export]
    pub use super::kv::KeyValue;

    #[pymodule_init]
    pub fn init(m: &Bound<PyModule>) -> PyResult<()> {
        Ok(())
    }
}
