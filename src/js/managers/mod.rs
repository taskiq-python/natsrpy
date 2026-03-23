pub mod consumers;
pub mod kv;
pub mod object_store;
pub mod streams;

#[pyo3::pymodule(submodule, name = "managers")]
pub mod pymod {
    #[pymodule_export]
    use super::consumers::ConsumersManager;
    #[pymodule_export]
    use super::kv::KVManager;
    #[pymodule_export]
    use super::object_store::ObjectStoreManager;
    #[pymodule_export]
    use super::streams::StreamsManager;
}
