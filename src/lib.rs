#![warn(
    // Base lints.
    clippy::all,
    // Some pedantic lints.
    clippy::pedantic,
    // New lints which are cool.
    clippy::nursery,
)]
#![
    allow(
        // I don't care about this.
        clippy::module_name_repetitions, 
        // Yo, the hell you should put
        // it in docs, if signature is clear as sky.
        clippy::missing_errors_doc,
        // Because pythonic way is
        // to have many args with defaults.
        clippy::too_many_arguments    
)]
pub mod exceptions;
pub mod js;
pub mod message;
pub mod nats_cls;
pub mod subscription;
pub mod utils;

#[pyo3::pymodule]
pub mod _inner {
    use pyo3::{Bound, PyResult, types::PyModule};

    use crate::utils::py::PyModuleSubmoduleExt;

    #[pymodule_export]
    use super::message::Message;
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
