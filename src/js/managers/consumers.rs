use std::{sync::Arc, time::Duration};

use futures_util::StreamExt;
use pyo3::{Bound, FromPyObject, IntoPyObjectExt, PyAny, PyRef, Python};
use tokio::sync::Mutex;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    js::consumers::{self, pull::PullConsumer, push::PushConsumer},
    utils::{natsrpy_future, py_types::TimeValue, streamer::Streamer},
};

#[pyo3::pyclass]
pub struct ConsumersIterator {
    streamer: Arc<
        Mutex<
            Streamer<
                Result<
                    async_nats::jetstream::consumer::Info,
                    async_nats::jetstream::stream::ConsumersError,
                >,
            >,
        >,
    >,
    stream: Arc<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
}

#[pyo3::pyclass]
pub struct ConsumersNamesIterator {
    streamer: Arc<Mutex<Streamer<Result<String, async_nats::jetstream::stream::ConsumersError>>>>,
}

impl ConsumersNamesIterator {
    #[must_use]
    pub fn new(
        streamer: Streamer<Result<String, async_nats::jetstream::stream::ConsumersError>>,
    ) -> Self {
        Self {
            streamer: Arc::new(Mutex::new(streamer)),
        }
    }
}

#[pyo3::pymethods]
impl ConsumersNamesIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.streamer.clone();
        natsrpy_future(py, async move {
            let value = ctx.lock().await.next().await;
            match value {
                Some(name) => Ok(name?),
                None => Err(NatsrpyError::AsyncStopIteration),
            }
        })
    }
}

impl ConsumersIterator {
    #[must_use]
    pub fn new(
        stream: Arc<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
        streamer: Streamer<
            Result<
                async_nats::jetstream::consumer::Info,
                async_nats::jetstream::stream::ConsumersError,
            >,
        >,
    ) -> Self {
        Self {
            stream,
            streamer: Arc::new(Mutex::new(streamer)),
        }
    }
}

#[pyo3::pymethods]
impl ConsumersIterator {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.streamer.clone();
        let stream = self.stream.clone();
        natsrpy_future(py, async move {
            let value = ctx.lock().await.next().await;
            match value {
                Some(info) => {
                    let info = info?;
                    let Some(consumer_name) = info.config.name else {
                        return Err(NatsrpyError::SessionError(String::from(
                            "Received consumer without a name.",
                        )));
                    };
                    // That means that the consumer is PushBased.
                    if info.config.deliver_subject.is_some() {
                        let consumer = consumers::push::consumer::PushConsumer::new(
                            stream.get_consumer(&consumer_name).await?,
                        );
                        Ok(Python::attach(|py| consumer.into_py_any(py))?)
                    } else {
                        let consumer = consumers::pull::consumer::PullConsumer::new(
                            stream.get_consumer(&consumer_name).await?,
                        );
                        Ok(Python::attach(|py| consumer.into_py_any(py))?)
                    }
                }
                None => Err(NatsrpyError::AsyncStopIteration),
            }
        })
    }
}

#[pyo3::pyclass]
pub struct ConsumersManager {
    stream: Arc<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
}

impl ConsumersManager {
    #[must_use]
    pub const fn new(
        stream: Arc<async_nats::jetstream::stream::Stream<async_nats::jetstream::stream::Info>>,
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
                    let consumer =
                        PullConsumer::new(ctx.create_consumer(config.try_into()?).await?);
                    Ok(Python::attach(|gil| consumer.into_py_any(gil))?)
                }
                ConsumerConfigs::Push(config) => {
                    let consumer =
                        PushConsumer::new(ctx.create_consumer(config.try_into()?).await?);
                    Ok(Python::attach(|gil| consumer.into_py_any(gil))?)
                }
            }
        })
    }

    pub fn update<'py>(
        &self,
        py: Python<'py>,
        config: ConsumerConfigs,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            match config {
                ConsumerConfigs::Pull(config) => {
                    let consumer =
                        PullConsumer::new(ctx.update_consumer(config.try_into()?).await?);
                    Ok(Python::attach(|gil| consumer.into_py_any(gil))?)
                }
                ConsumerConfigs::Push(config) => {
                    let consumer =
                        PushConsumer::new(ctx.update_consumer(config.try_into()?).await?);
                    Ok(Python::attach(|gil| consumer.into_py_any(gil))?)
                }
            }
        })
    }

    pub fn get_pull<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            Ok(consumers::pull::consumer::PullConsumer::new(
                ctx.get_consumer(&name).await?,
            ))
        })
    }

    pub fn get_push<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            Ok(consumers::push::consumer::PushConsumer::new(
                ctx.get_consumer(&name).await?,
            ))
        })
    }

    pub fn pause<'py>(
        &self,
        py: Python<'py>,
        name: String,
        delay: TimeValue,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        let untill = time::OffsetDateTime::now_utc() + Duration::from(delay);
        natsrpy_future(py, async move {
            Ok(ctx.pause_consumer(&name, untill).await?.paused)
        })
    }

    pub fn resume<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(
            py,
            async move { Ok(ctx.resume_consumer(&name).await?.paused) },
        )
    }

    pub fn delete<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(
            py,
            async move { Ok(ctx.delete_consumer(&name).await?.success) },
        )
    }

    pub fn list<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            let consumers = ctx.consumers();
            Ok(ConsumersIterator::new(
                ctx.clone(),
                Streamer::new(consumers),
            ))
        })
    }

    pub fn list_names<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.stream.clone();
        natsrpy_future(py, async move {
            let consumers = ctx.consumer_names();
            Ok(ConsumersNamesIterator::new(Streamer::new(consumers)))
        })
    }
}
