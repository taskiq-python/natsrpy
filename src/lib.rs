use pyo3::prelude::*;

pub mod exceptions;
pub mod jetstream;
pub mod nats_cls;
pub mod subscription;
pub mod utils;

/// A Python module implemented in Rust.
#[pymodule]
mod _internal {
    use pyo3::types::PyModule;
    use pyo3::{Bound, PyResult};

    #[pymodule_export]
    use crate::jetstream::pymod;

    #[pymodule_export]
    use crate::nats_cls::NatsCls;

    #[pymodule_export]
    use crate::subscription::Subscription;

    #[pymodule_export]
    use crate::exceptions::py_err::inner;

    #[pymodule_init]
    fn init(_: &Bound<'_, PyModule>) -> PyResult<()> {
        // Initialize logging interpop.
        pyo3_log::init();
        Ok(())
    }
}
