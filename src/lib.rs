pub mod exceptions;
pub mod js;
pub mod nats_cls;
pub mod subscription;
pub mod utils;
pub mod message;

#[pyo3::pymodule]
pub mod _inner {
    use pyo3::{Bound, PyResult, types::PyModule};

    use crate::utils::py::PyModuleSubmoduleExt;

    #[pymodule_export]
    use super::nats_cls::NatsCls;
    #[pymodule_export]
    use super::subscription::Subscription;

    #[pymodule_export]
    use super::js::pymod as js;

    #[pymodule_init]
    pub fn init(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.init_submodules()?;
        Ok(())
    }
}
