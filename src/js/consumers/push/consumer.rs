use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, PyRef, Python};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::pymod::JetStreamMessage,
    utils::natsrpy_future,
};

type NatsPushConsumer =
    async_nats::jetstream::consumer::Consumer<async_nats::jetstream::consumer::push::Config>;

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct PushConsumer {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    stream_name: String,
    consumer: Arc<NatsPushConsumer>,
}

impl PushConsumer {
    #[must_use]
    pub fn new(consumer: NatsPushConsumer) -> Self {
        let info = consumer.cached_info();
        Self {
            name: info.name.clone(),
            stream_name: info.stream_name.clone(),
            consumer: Arc::new(consumer),
        }
    }
}

#[pyo3::pyclass]
pub struct PushConsumerContextManager {
    context: Arc<NatsPushConsumer>,
}

impl PushConsumerContextManager {
    #[must_use]
    pub const fn new(context: Arc<NatsPushConsumer>) -> Self {
        Self { context }
    }
}

#[pyo3::pymethods]
impl PushConsumerContextManager {
    pub fn __aenter__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let consumer = self.context.clone();
        natsrpy_future(py, async move {
            Ok(MessagesIterator::from(consumer.messages().await?))
        })
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
        natsrpy_future(py, async move { Ok(()) })
    }
}

#[pyo3::pyclass]
pub struct MessagesIterator {
    messages: Option<Arc<tokio::sync::Mutex<async_nats::jetstream::consumer::push::Messages>>>,
}

impl From<async_nats::jetstream::consumer::push::Messages> for MessagesIterator {
    fn from(value: async_nats::jetstream::consumer::push::Messages) -> Self {
        Self {
            messages: Some(Arc::new(tokio::sync::Mutex::new(value))),
        }
    }
}

#[pyo3::pymethods]
impl PushConsumer {
    #[must_use]
    pub fn consume(&self) -> PushConsumerContextManager {
        PushConsumerContextManager::new(self.consumer.clone())
    }

    #[must_use]
    pub fn __repr__(&self) -> String {
        format!(
            "PushConsumer<name={name:?}, stream_name={stream_name:?}>",
            name = self.name,
            stream_name = self.stream_name
        )
    }
}

#[pyo3::pymethods]
impl MessagesIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(messages_guard) = self.messages.clone() else {
            unreachable!("Message is always Some in runtime.")
        };
        #[allow(clippy::significant_drop_tightening)]
        natsrpy_future(py, async move {
            let mut messages = messages_guard.lock().await;
            let Some(message) = messages.next().await else {
                return Err(NatsrpyError::AsyncStopIteration);
            };
            let message = message?;

            JetStreamMessage::try_from(message)
        })
    }
}

impl Drop for MessagesIterator {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            self.messages = None;
        });
    }
}
