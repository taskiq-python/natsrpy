use std::sync::Arc;

use crate::js::stream::Stream;
use pyo3::{Bound, PyAny, Python};

use crate::{exceptions::rust_err::NatsrpyResult, js::stream::StreamConfig, utils::natsrpy_future};

#[pyo3::pyclass]
pub struct StreamsManager {
    ctx: Arc<async_nats::jetstream::Context>,
}

impl StreamsManager {
    #[must_use]
    pub const fn new(ctx: Arc<async_nats::jetstream::Context>) -> Self {
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
            Ok(Stream::new(
                ctx.create_stream(async_nats::jetstream::stream::Config::try_from(config)?)
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
                .create_or_update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Stream::new(ctx.get_stream(info.config.name).await?))
        })
    }

    pub fn get<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(
            py,
            async move { Ok(Stream::new(ctx.get_stream(name).await?)) },
        )
    }

    pub fn delete<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(
            py,
            async move { Ok(ctx.delete_stream(name).await?.success) },
        )
    }

    pub fn update<'py>(
        &self,
        py: Python<'py>,
        config: StreamConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = ctx
                .update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Stream::new(ctx.get_stream(info.config.name).await?))
        })
    }
}
