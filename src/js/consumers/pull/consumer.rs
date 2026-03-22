use std::{sync::Arc, time::Duration};

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, Python};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::NatsrpyResult,
    utils::{futures::natsrpy_future_with_timeout, py_types::TimeValue},
};

type NatsPullConsumer =
    async_nats::jetstream::consumer::Consumer<async_nats::jetstream::consumer::pull::Config>;

#[pyo3::pyclass(from_py_object)]
#[derive(Debug, Clone)]
pub struct PullConsumer {
    consumer: Arc<RwLock<NatsPullConsumer>>,
}

impl PullConsumer {
    #[must_use]
    pub fn new(consumer: NatsPullConsumer) -> Self {
        Self {
            consumer: Arc::new(RwLock::new(consumer)),
        }
    }
}

#[pyo3::pymethods]
impl PullConsumer {
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
        heartbeat: Option<Duration>,
        expires: Option<Duration>,
        min_pending: Option<usize>,
        min_ack_pending: Option<usize>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.consumer.clone();

        // Because we borrow cosnumer lock
        // later for modifications of fetchbuilder.
        #[allow(clippy::significant_drop_tightening)]
        natsrpy_future_with_timeout(py, timeout, async move {
            let consumer = ctx.read().await;
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
                fetch_builder = fetch_builder.heartbeat(heartbeat);
            }
            if let Some(expires) = expires {
                fetch_builder = fetch_builder.expires(expires);
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
}
