use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, Python};
use tokio::sync::RwLock;

use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

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

#[pyo3::pyclass]
pub struct PullMessageIterator {
    inner: Arc<RwLock<async_nats::jetstream::consumer::pull::Batch>>,
}

#[pyo3::pymethods]
impl PullConsumer {
    pub fn messages<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let consumer_lock = self.consumer.clone();
        natsrpy_future(py, async move {
            let mut messages = consumer_lock.read().await.messages().await.unwrap();
            while let Some(message) = messages.next().await {
                let msg = message?;
                log::info!("{:#?}", msg.message.payload);
                msg.ack().await?;
            }

            Ok(())
        })
    }
}

#[pyo3::pymethods]
impl PullMessageIterator {}
