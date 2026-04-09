use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, PyRef, Python};

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::pymod::JetStreamMessage,
    utils::{
        futures::natsrpy_future_with_timeout, natsrpy_future, py_types::TimeValue,
        streamer::Streamer,
    },
};

type NatsPullConsumer =
    async_nats::jetstream::consumer::Consumer<async_nats::jetstream::consumer::pull::Config>;

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct PullConsumer {
    #[pyo3(get)]
    name: String,
    #[pyo3(get)]
    stream_name: String,
    consumer: Arc<NatsPullConsumer>,
}

impl PullConsumer {
    #[must_use]
    pub fn new(consumer: NatsPullConsumer) -> Self {
        let info = consumer.cached_info();
        Self {
            name: info.name.clone(),
            stream_name: info.stream_name.clone(),
            consumer: Arc::new(consumer),
        }
    }
}

#[pyo3::pyclass]
pub struct PullConsumerFetcher {
    pub consumer: Arc<NatsPullConsumer>,
    pub messages: Arc<
        tokio::sync::Mutex<
            Streamer<
                Result<
                    async_nats::jetstream::Message,
                    async_nats::jetstream::consumer::pull::MessagesError,
                >,
            >,
        >,
    >,
}

impl PullConsumerFetcher {
    #[must_use]
    pub fn new(
        consumer: Arc<NatsPullConsumer>,
        messages: async_nats::jetstream::consumer::pull::Stream,
    ) -> Self {
        Self {
            consumer,
            messages: Arc::new(tokio::sync::Mutex::new(Streamer::new(messages))),
        }
    }
}

#[pyo3::pymethods]
impl PullConsumerFetcher {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.messages.clone();
        natsrpy_future(py, async move {
            let value = ctx.lock().await.next().await;
            match value {
                Some(info) => JetStreamMessage::try_from(info?),
                None => Err(NatsrpyError::AsyncStopIteration),
            }
        })
    }
}

#[pyo3::pyclass]
pub struct PullConsumerContextManager {
    consumer: Arc<NatsPullConsumer>,
}

impl PullConsumerContextManager {
    #[must_use]
    pub const fn new(consumer: Arc<NatsPullConsumer>) -> Self {
        Self { consumer }
    }
}

#[pyo3::pymethods]
impl PullConsumerContextManager {
    pub fn __aenter__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let consumer = self.consumer.clone();
        natsrpy_future(py, async move {
            let messages = consumer.messages().await?;
            Ok(PullConsumerFetcher::new(consumer, messages))
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

#[pyo3::pymethods]
impl PullConsumer {
    #[must_use]
    pub fn consume(&self) -> PullConsumerContextManager {
        PullConsumerContextManager::new(self.consumer.clone())
    }

    #[pyo3(signature=(
        max_messages=None,
        group=None,
        priority=None,
        max_bytes=None,
        heartbeat=None,
        expires=None,
        min_pending=None,
        min_ack_pending=None,
        timeout=None,
    ))]
    pub fn fetch<'py>(
        &self,
        py: Python<'py>,
        max_messages: Option<usize>,
        group: Option<String>,
        priority: Option<usize>,
        max_bytes: Option<usize>,
        heartbeat: Option<TimeValue>,
        expires: Option<TimeValue>,
        min_pending: Option<usize>,
        min_ack_pending: Option<usize>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let consumer = self.consumer.clone();
        #[allow(clippy::significant_drop_tightening)]
        natsrpy_future_with_timeout(py, timeout, async move {
            let mut fetch_builder = consumer.fetch();
            if let Some(max_messages) = max_messages {
                fetch_builder = fetch_builder.max_messages(max_messages);
            }
            if let Some(group) = group {
                fetch_builder = fetch_builder.group(group);
            }
            if let Some(priority) = priority {
                fetch_builder = fetch_builder.priority(priority);
            }
            if let Some(max_bytes) = max_bytes {
                fetch_builder = fetch_builder.max_bytes(max_bytes);
            }
            if let Some(heartbeat) = heartbeat {
                fetch_builder = fetch_builder.heartbeat(heartbeat.into());
            }
            if let Some(expires) = expires {
                fetch_builder = fetch_builder.expires(expires.into());
            }
            if let Some(min_pending) = min_pending {
                fetch_builder = fetch_builder.min_pending(min_pending);
            }
            if let Some(min_ack_pending) = min_ack_pending {
                fetch_builder = fetch_builder.min_ack_pending(min_ack_pending);
            }
            let mut messages = fetch_builder.messages().await?;
            let mut ret_messages = Vec::new();
            while let Some(msg) = messages.next().await {
                let raw_msg = msg?;
                ret_messages.push(crate::js::message::JetStreamMessage::try_from(raw_msg)?);
            }
            Ok(ret_messages)
        })
    }

    #[must_use]
    pub fn __repr__(&self) -> String {
        format!(
            "PullConsumer<name={name:?}, stream_name={stream_name:?}>",
            name = self.name,
            stream_name = self.stream_name
        )
    }
}
