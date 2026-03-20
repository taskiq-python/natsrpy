use std::sync::Arc;

use crate::js::stream::Stream;
use pyo3::{Bound, PyAny, Python};
use tokio::sync::RwLock;

use crate::{exceptions::rust_err::NatsrpyResult, js::stream::StreamConfig, utils::natsrpy_future};

#[pyo3::pyclass]
pub struct StreamsManager {
    ctx: Arc<RwLock<async_nats::jetstream::Context>>,
}

impl StreamsManager {
    pub const fn new(ctx: Arc<RwLock<async_nats::jetstream::Context>>) -> Self {
        Self { ctx }
    }
}

#[pyo3::pymethods]
impl StreamsManager {
    pub fn create<'py>(
        &self,
        py: Python<'py>,
        config: StreamConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(Stream::new(
                js.create_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                    .await?,
            ))
        })
    }

    pub fn create_or_update<'py>(
        &self,
        py: Python<'py>,
        config: StreamConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = ctx
                .read()
                .await
                .create_or_update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Stream::new(
                ctx.read().await.get_stream(info.config.name).await?,
            ))
        })
    }

    pub fn get<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(Stream::new(ctx.read().await.get_stream(name).await?))
        })
    }

    pub fn delete<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(js.delete_stream(name).await?.success)
        })
    }

    pub fn update<'py>(
        &self,
        py: Python<'py>,
        config: StreamConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = ctx
                .read()
                .await
                .update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Stream::new(
                ctx.read().await.get_stream(info.config.name).await?,
            ))
        })
    }
}
