#![deny(
    // Base lints.
    clippy::all,
    // Some pedantic lints.
    clippy::pedantic,
    // New lints which are cool.
    clippy::nursery,
)]
#![
    allow(
        // Beacsue some types naming conventions are
        // just different to the ones that rust have.
        non_camel_case_types,
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
pub mod subscriptions;
pub mod utils;

#[pyo3::pymodule]
pub mod _natsrpy_rs {
    use pyo3::{Bound, PyResult, types::PyModule};

    use crate::utils::py::PyModuleSubmoduleExt;

    #[pymodule_export]
    use super::message::Message;
    #[pymodule_export]
    use super::nats_cls::NatsCls;
    #[pymodule_export]
    use super::subscriptions::{
        callback::CallbackSubscription, ctx_manager::SubscriptionCtxManager,
        iterator::IteratorSubscription,
    };

    #[pymodule_export]
    use super::exceptions::py_err::pymod as exceptions;

    #[pymodule_export]
    use super::js::pymod as js;

    #[pymodule_init]
    pub fn init(m: &Bound<'_, PyModule>) -> PyResult<()> {
        pyo3_log::init();
        m.init_submodules()?;
        Ok(())
    }
}
