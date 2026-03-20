use std::sync::Arc;

use pyo3::{Bound, FromPyObject, IntoPyObjectExt, PyAny, Python};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::consumers::{self, pull::PullConsumer, push::PushConsumer},
    utils::natsrpy_future,
};

#[pyo3::pyclass]
pub struct ConsumersManager {
    stream: Arc<RwLock<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>>,
}

impl ConsumersManager {
    pub const fn new(
        stream: Arc<
            RwLock<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
        >,
    ) -> Self {
        Self { stream }
    }
}

pub enum ConsumerConfigs {
    Pull(consumers::pull::PullConsumerConfig),
    Push(consumers::push::PushConsumerConfig),
}

impl<'py> FromPyObject<'_, 'py> for ConsumerConfigs {
    type Error = NatsrpyError;

    fn extract(obj: pyo3::Borrowed<'_, 'py, PyAny>) -> Result<Self, Self::Error> {
        #[allow(clippy::option_if_let_else)]
        if let Ok(conf) = obj.extract::<consumers::pull::PullConsumerConfig>() {
            Ok(Self::Pull(conf))
        } else if let Ok(conf) = obj.extract::<consumers::push::PushConsumerConfig>() {
            Ok(Self::Push(conf))
        } else {
            Err(NatsrpyError::InvalidArgument(String::from(
                "Unknown value passed as consumer config. Only consumer config classes are accepted.",
            )))
        }
    }
}

#[pyo3::pyclass]
pub enum Consumers {
    Pull(consumers::pull::PullConsumer),
    Push(consumers::push::PushConsumer),
}

#[pyo3::pymethods]
impl ConsumersManager {
    pub fn create<'py>(
        &self,
        py: Python<'py>,
        config: ConsumerConfigs,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            match config {
                ConsumerConfigs::Pull(config) => {
                    let consumer = PullConsumer::new(
                        ctx.read().await.create_consumer(config.try_into()?).await?,
                    );
                    Ok(Python::attach(|gil| consumer.into_py_any(gil))?)
                }
                ConsumerConfigs::Push(config) => {
                    let consumer = PushConsumer::new(
                        ctx.read().await.create_consumer(config.try_into()?).await?,
                    );
                    Ok(Python::attach(|gil| consumer.into_py_any(gil))?)
                }
            }
        })
    }

    pub fn get<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            Ok(consumers::pull::consumer::PullConsumer::new(
                ctx.read().await.get_consumer(&name).await?,
            ))
        })
    }
}
