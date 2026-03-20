use std::sync::Arc;

use tokio::sync::RwLock;


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
impl PullConsumer {}

#[pyo3::pymethods]
impl PullMessageIterator {}
