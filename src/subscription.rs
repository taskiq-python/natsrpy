use futures_util::StreamExt;
use std::sync::Arc;

use pyo3::{Bound, PyAny, PyRef, Python};
use tokio::sync::Mutex;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::{futures::natsrpy_future_with_timeout, py_types::TimeValue},
};

#[pyo3::pyclass]
pub struct Subscription {
    inner: Option<Arc<Mutex<async_nats::Subscriber>>>,
}

impl Subscription {
    #[must_use]
    pub fn new(sub: async_nats::Subscriber) -> Self {
        Self {
            inner: Some(Arc::new(Mutex::new(sub))),
        }
    }
}

#[pyo3::pymethods]
impl Subscription {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn next<'py>(
        &self,
        py: Python<'py>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(inner) = self.inner.clone() else {
            return Err(NatsrpyError::NotInitialized);
        };
        natsrpy_future_with_timeout(py, timeout, async move {
            let Some(message) = inner.lock().await.next().await else {
                return Err(NatsrpyError::AsyncStopIteration);
            };

            crate::message::Message::try_from(message)
        })
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.next(py, None)
    }
}

/// This is required only because
/// in nats library they run async operation on Drop.
///
/// Because of that we need to execute drop in async
/// runtime's context.
///
/// And because we want to perform a drop,
/// we need somehow drop the inner variable,
/// but leave self intouch. That is exactly why we have
/// Option<Arc<...>>. So we can just assign it to None
/// and it will perform a drop.
impl Drop for Subscription {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            self.inner = None;
        });
    }
}
