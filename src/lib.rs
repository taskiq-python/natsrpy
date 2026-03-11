use pyo3::{
    Bound, PyResult,
    types::{PyModule, PyModuleMethods},
};

pub mod exceptions;
pub mod js;
pub mod nats_cls;
pub mod subscription;
pub mod utils;

/// A Python module implemented in Rust.
#[pyo3::pymodule]
pub mod _inner {
    use pyo3::{Bound, PyResult, types::PyModule};

    use crate::utils::py::PyModuleExt;

    #[pymodule_export]
    use super::nats_cls::NatsCls;
    #[pymodule_export]
    use super::subscription::Subscription;

    #[pymodule_init]
    pub fn init(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.attach_submodule_with_sys(m.py(), pyo3::wrap_pymodule!(super::exceptions::py_err::pymod))?;
        m.attach_submodule_with_sys(m.py(), pyo3::wrap_pymodule!(super::js::pymod))?;
        Ok(())
    }
}
