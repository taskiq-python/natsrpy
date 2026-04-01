use std::sync::Arc;

use pyo3::{Bound, IntoPyObjectExt, Py, PyAny, Python};

use crate::{
    exceptions::rust_err::NatsrpyResult,
    subscriptions::{callback::CallbackSubscription, iterator::IteratorSubscription},
    utils::natsrpy_future,
};

#[pyo3::pyclass]
pub struct SubscriptionCtxManager {
    client: async_nats::Client,
    subject: String,
    callback: Option<Py<PyAny>>,
    queue: Option<String>,
    current_sub: Arc<tokio::sync::Mutex<Option<Py<PyAny>>>>,
}

impl SubscriptionCtxManager {
    #[must_use]
    pub fn new(
        client: async_nats::Client,
        subject: String,
        callback: Option<Py<PyAny>>,
        queue: Option<String>,
    ) -> Self {
        Self {
            client,
            subject,
            callback,
            queue,
            current_sub: Arc::new(tokio::sync::Mutex::new(None)),
        }
    }
}

#[pyo3::pymethods]
impl SubscriptionCtxManager {
    pub fn __aenter__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let current_sub = self.current_sub.clone();
        let client = self.client.clone();
        let callback = self.callback.as_ref().map(|val| val.clone_ref(py));
        let subject = self.subject.clone();
        let queue = self.queue.clone();
        #[allow(clippy::significant_drop_tightening)]
        natsrpy_future(py, async move {
            let mut current_sub = current_sub.lock().await;
            if current_sub.is_some() {
                return Err(crate::exceptions::rust_err::NatsrpyError::SessionError(
                    String::from(
                        "Subscription context manager is already active. Cannot enter a new context until the current one is exited.",
                    ),
                ));
            }
            let subscriber = if let Some(queue) = queue {
                client.queue_subscribe(subject, queue).await?
            } else {
                client.subscribe(subject).await?
            };
            if let Some(cb) = callback {
                let sub = CallbackSubscription::new(subscriber, cb)?;
                Python::attach(|gil| -> NatsrpyResult<_> {
                    let sub = sub.into_bound_py_any(gil)?;
                    *current_sub = Some(sub.clone().unbind());
                    Ok(sub.unbind())
                })
            } else {
                let sub = IteratorSubscription::new(subscriber);
                Python::attach(|gil| -> NatsrpyResult<_> {
                    let sub = sub.into_bound_py_any(gil)?;
                    *current_sub = Some(sub.clone().unbind());
                    Ok(sub.unbind())
                })
            }
        })
    }

    pub fn detatch<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.__aenter__(py)
    }

    #[pyo3(signature=(
        _exc_type=None,
        _exc_val=None,
        _exc_tb=None,
    ))]
    pub fn __aexit__<'py>(
        &self,
        py: Python<'py>,
        _exc_type: Option<Bound<'py, PyAny>>,
        _exc_val: Option<Bound<'py, PyAny>>,
        _exc_tb: Option<Bound<'py, PyAny>>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let current_sub = self.current_sub.clone();
        #[allow(clippy::significant_drop_tightening)]
        natsrpy_future(py, async move {
            let mut current_sub = current_sub.lock().await;
            *current_sub = None;
            Ok(())
        })
    }
}
