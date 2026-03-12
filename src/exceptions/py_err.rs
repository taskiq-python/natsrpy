use pyo3::{create_exception, pymodule};

create_exception!(
    natsrpy.exceptions,
    NatsrpyBaseError,
    pyo3::exceptions::PyException
);

create_exception!(natsrpy.exceptions, NatsrpySessionError, NatsrpyBaseError);
create_exception!(natsrpy.exceptions, NatsrpyPublishError, NatsrpyBaseError);

#[pymodule(submodule, name = "exceptions")]
pub mod pymod {
    #[pymodule_export]
    use super::{NatsrpyBaseError, NatsrpyPublishError, NatsrpySessionError};
}
