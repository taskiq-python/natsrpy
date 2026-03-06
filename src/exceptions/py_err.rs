use pyo3::create_exception;
use pyo3::pymodule;

create_exception!(
    natsrpy.exceptions,
    NatsrpyBaseError,
    pyo3::exceptions::PyException
);

create_exception!(natsrpy.exceptions, NatsrpySessionError, NatsrpyBaseError);
create_exception!(natsrpy.exceptions, NatsrpyPublishError, NatsrpyBaseError);

#[pymodule(name = "exceptions")]
pub mod inner {
    #[pymodule_export]
    use super::{NatsrpyBaseError, NatsrpySessionError};
}
