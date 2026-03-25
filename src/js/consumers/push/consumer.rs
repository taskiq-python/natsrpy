use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, PyRef, Python};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::pymod::JetStreamMessage,
    utils::{futures::natsrpy_future_with_timeout, natsrpy_future, py_types::TimeValue},
};

type NatsPushConsumer =
    async_nats::jetstream::consumer::Consumer<async_nats::jetstream::consumer::push::Config>;

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct PushConsumer {
    consumer: Arc<RwLock<NatsPushConsumer>>,
}

impl PushConsumer {
    #[must_use]
    pub fn new(consumer: NatsPushConsumer) -> Self {
        Self {
            consumer: Arc::new(RwLock::new(consumer)),
        }
    }
}

#[pyo3::pyclass]
pub struct MessagesIterator {
    messages: Option<Arc<RwLock<async_nats::jetstream::consumer::push::Messages>>>,
}

impl From<async_nats::jetstream::consumer::push::Messages> for MessagesIterator {
    fn from(value: async_nats::jetstream::consumer::push::Messages) -> Self {
        Self {
            messages: Some(Arc::new(RwLock::new(value))),
        }
    }
}

#[pyo3::pymethods]
impl PushConsumer {
    pub fn messages<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let consumer_guard = self.consumer.clone();
        natsrpy_future(py, async move {
            Ok(MessagesIterator::from(
                consumer_guard.read().await.messages().await?,
            ))
        })
    }
}

#[pyo3::pymethods]
impl MessagesIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    #[pyo3(signature=(timeout=None))]
    pub fn next<'py>(
        &self,
        py: Python<'py>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(messages_guard) = self.messages.clone() else {
            unreachable!("Message is always Some in runtime.")
        };
        #[allow(clippy::significant_drop_tightening)]
        natsrpy_future_with_timeout(py, timeout, async move {
            let mut messages = messages_guard.write().await;
            let Some(message) = messages.next().await else {
                return Err(NatsrpyError::AsyncStopIteration);
            };
            let message = message?;

            JetStreamMessage::try_from(message)
        })
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.next(py, None)
    }
}

impl Drop for MessagesIterator {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            self.messages = None;
        });
    }
}
