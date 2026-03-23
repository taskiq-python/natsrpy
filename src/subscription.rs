use futures_util::StreamExt;
use std::sync::Arc;

use pyo3::{Bound, Py, PyAny, PyRef, Python};
use tokio::sync::Mutex;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::{futures::natsrpy_future_with_timeout, natsrpy_future, py_types::TimeValue},
};

#[pyo3::pyclass]
pub struct Subscription {
    inner: Option<Arc<Mutex<async_nats::Subscriber>>>,
    reading_task: Option<tokio::task::AbortHandle>,
}

async fn process_message(message: async_nats::message::Message, py_callback: Py<PyAny>) {
    let task = async || -> NatsrpyResult<()> {
        let message = crate::message::Message::try_from(&message)?;
        let awaitable = Python::attach(|gil| -> NatsrpyResult<_> {
            let res = py_callback.call1(gil, (message,))?;
            let rust_task = pyo3_async_runtimes::tokio::into_future(res.into_bound(gil))?;
            Ok(rust_task)
        })?;
        awaitable.await?;
        Ok(())
    };
    if let Err(err) = task().await {
        log::error!("Cannot process message {message:?}. Error: {err}");
    }
}

async fn start_py_sub(
    sub: Arc<Mutex<async_nats::Subscriber>>,
    py_callback: Py<PyAny>,
    locals: pyo3_async_runtimes::TaskLocals,
) {
    while let Some(message) = sub.lock().await.next().await {
        let py_cb = Python::attach(|py| py_callback.clone_ref(py));
        tokio::spawn(pyo3_async_runtimes::tokio::scope(
            locals.clone(),
            process_message(message, py_cb),
        ));
    }
}

impl Subscription {
    pub fn new(sub: async_nats::Subscriber, callback: Option<Py<PyAny>>) -> NatsrpyResult<Self> {
        let sub = Arc::new(Mutex::new(sub));
        let cb_sub = sub.clone();
        let task_locals = Python::attach(pyo3_async_runtimes::tokio::get_current_locals)?;
        let task_handle = callback.map(move |cb| {
            tokio::task::spawn(pyo3_async_runtimes::tokio::scope(
                task_locals.clone(),
                start_py_sub(cb_sub, cb, task_locals),
            ))
            .abort_handle()
        });

        Ok(Self {
            inner: Some(sub),
            reading_task: task_handle,
        })
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
            unreachable!("Subscription used after del")
        };
        if self.reading_task.is_some() {
            log::warn!(
                "Callback is set. Getting messages from this subscription might produce unpredictable results."
            );
        }
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
impl Drop for Subscription {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            self.inner = None;
            if let Some(reading) = self.reading_task.take() {
                reading.abort();
            }
        });
    }
}
