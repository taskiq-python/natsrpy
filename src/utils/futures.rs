use pyo3::{Bound, IntoPyObject, PyAny, Python};

use crate::exceptions::rust_err::NatsrpyResult;

pub fn natsrpy_future<F, T>(py: Python, fut: F) -> NatsrpyResult<Bound<PyAny>>
where
    F: Future<Output = NatsrpyResult<T>> + Send + 'static,
    T: for<'py> IntoPyObject<'py> + Send + 'static,
{
    let res =
        pyo3_async_runtimes::tokio::future_into_py(py, async { fut.await.map_err(Into::into) })
            .map(Into::into)?;
    Ok(res)
}
