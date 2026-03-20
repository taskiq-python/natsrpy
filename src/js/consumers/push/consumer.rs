use std::sync::Arc;

use tokio::sync::RwLock;

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

#[pyo3::pymethods]
impl PushConsumer {}
