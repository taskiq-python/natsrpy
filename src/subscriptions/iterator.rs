use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, PyRef, Python};
use tokio::sync::Mutex;

use crate::exceptions::rust_err::{NatsrpyError, NatsrpyResult};
use crate::utils::futures::natsrpy_future_with_timeout;
use crate::utils::natsrpy_future;
use crate::utils::py_types::TimeValue;

#[pyo3::pyclass]
pub struct IteratorSubscription {
    inner: Option<Arc<Mutex<async_nats::Subscriber>>>,
}

impl IteratorSubscription {
    #[must_use]
    pub fn new(sub: async_nats::Subscriber) -> Self {
        Self {
            inner: Some(Arc::new(Mutex::new(sub))),
        }
    }
}

#[pyo3::pymethods]
impl IteratorSubscription {
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
            unreachable!("Subscription used after del")
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

    #[pyo3(signature=(limit=None))]
    pub fn unsubscribe<'py>(
        &self,
        py: Python<'py>,
        limit: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(inner) = self.inner.clone() else {
            unreachable!("Subscription used after del")
        };
        natsrpy_future(py, async move {
            if let Some(limit) = limit {
                inner.lock().await.unsubscribe_after(limit).await?;
            } else {
                inner.lock().await.unsubscribe().await?;
            }
            Ok(())
        })
    }

    pub fn drain<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(inner) = self.inner.clone() else {
            unreachable!("Subscription used after del")
        };
        natsrpy_future(py, async move {
            inner.lock().await.drain().await?;
            Ok(())
        })
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
impl Drop for IteratorSubscription {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            self.inner = None;
        });
    }
}
