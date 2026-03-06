use futures_util::StreamExt;
use pyo3::exceptions::PyStopAsyncIteration;
use std::{sync::Arc, time::Duration};

use pyo3::Py;
use pyo3::types::PyBytes;
use pyo3::{Bound, IntoPyObjectExt, PyAny, PyRef, Python, pyclass, pymethods};
use tokio::sync::Mutex;

use crate::exceptions::rust_err::NatsrpyError;
use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

#[pyclass]
pub struct Message {
    #[pyo3(get)]
    subject: String,
    #[pyo3(get)]
    reply: Option<String>,
    #[pyo3(get)]
    payload: Py<PyBytes>,
}

#[pyclass]
pub struct Subscription {
    inner: Option<Arc<Mutex<async_nats::Subscriber>>>,
}

impl Subscription {
    pub fn new(sub: async_nats::Subscriber) -> Self {
        Self {
            inner: Some(Arc::new(Mutex::new(sub))),
        }
    }
}

#[pymethods]
impl Subscription {
    #[must_use]
    pub fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn next<'a>(
        &self,
        py: Python<'a>,
        timeout: Option<f32>,
    ) -> NatsrpyResult<Bound<'a, PyAny>> {
        let Some(inner) = self.inner.clone() else {
            return Err(NatsrpyError::NotInitialized);
        };

        let future = async move {
            let mut guard = inner.lock().await;
            let Some(message) = guard.next().await else {
                return Err(NatsrpyError::from(PyStopAsyncIteration::new_err(
                    "End of the stream.",
                )));
            };

            Python::attach(move |gil| -> NatsrpyResult<_> {
                let data = PyBytes::new(gil, message.payload.as_ref()).unbind();
                Ok(Message {
                    subject: message.subject.to_string(),
                    reply: message.reply.map(|subj| subj.to_string()),
                    payload: data,
                })
            })
        };

        natsrpy_future(py, async move {
            if let Some(timeout) = timeout {
                tokio::time::timeout(Duration::from_secs_f32(timeout), future).await?
            } else {
                future.await
            }
        })
    }

    pub fn __anext__<'a>(&self, py: Python<'a>) -> NatsrpyResult<Bound<'a, PyAny>> {
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
