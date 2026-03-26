use std::time::Duration;

use pyo3::{Bound, IntoPyObject, PyAny, Python};

use crate::exceptions::rust_err::{NatsrpyError, NatsrpyResult};

pub fn natsrpy_future<F, T>(py: Python, fut: F) -> NatsrpyResult<Bound<PyAny>>
where
    F: Future<Output = NatsrpyResult<T>> + Send + 'static,
    T: for<'py> IntoPyObject<'py> + Send + 'static,
{
    let res =
        pyo3_async_runtimes::tokio::future_into_py(py, async { fut.await.map_err(Into::into) })?;
    Ok(res)
}

#[inline]
pub fn natsrpy_future_with_timeout<F, T, D>(
    py: Python,
    timeout: Option<D>,
    fut: F,
) -> NatsrpyResult<Bound<PyAny>>
where
    F: Future<Output = NatsrpyResult<T>> + Send + 'static,
    T: for<'py> IntoPyObject<'py> + Send + 'static,
    D: Into<Duration>,
{
    let timeout = timeout.map(Into::into);
    let res = pyo3_async_runtimes::tokio::future_into_py(py, async move {
        if let Some(timeout) = timeout {
            tokio::time::timeout(timeout, fut)
                .await
                // First map_err is for timeout
                .map_err(NatsrpyError::from)?
                // This one is for result returned from
                // a future.
                .map_err(Into::into)
        } else {
            // Simple return with error mapping.
            fut.await.map_err(Into::into)
        }
    })?;
    Ok(res)
}
