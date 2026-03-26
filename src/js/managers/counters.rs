use std::sync::Arc;

use crate::{
    exceptions::rust_err::NatsrpyError,
    js::counters::{Counters, CountersConfig},
};
use pyo3::{Bound, PyAny, Python};
use tokio::sync::RwLock;

use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

#[pyo3::pyclass]
pub struct CountersManager {
    ctx: Arc<RwLock<async_nats::jetstream::Context>>,
}

impl CountersManager {
    pub const fn new(ctx: Arc<RwLock<async_nats::jetstream::Context>>) -> Self {
        Self { ctx }
    }
}

#[pyo3::pymethods]
impl CountersManager {
    pub fn create<'py>(
        &self,
        py: Python<'py>,
        config: CountersConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let js = ctx.read().await;
            Ok(Counters::new(
                js.create_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                    .await?,
                ctx.clone(),
            ))
        })
    }

    pub fn create_or_update<'py>(
        &self,
        py: Python<'py>,
        config: CountersConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = ctx
                .read()
                .await
                .create_or_update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Counters::new(
                ctx.read().await.get_stream(info.config.name).await?,
                ctx.clone(),
            ))
        })
    }

    pub fn get<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let stream = ctx.read().await.get_stream(&name).await?;
            let config = stream.get_info().await?.config;
            if !config.allow_direct {
                return Err(NatsrpyError::SessionError(format!(
                    "Stream {name} doesn't allow direct get.",
                )));
            }
            if !config.allow_message_counter {
                return Err(NatsrpyError::SessionError(format!(
                    "Stream {name} doesn't allow message counters.",
                )));
            }
            Ok(Counters::new(stream, ctx.clone()))
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
        config: CountersConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = ctx
                .read()
                .await
                .update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Counters::new(
                ctx.read().await.get_stream(info.config.name).await?,
                ctx.clone(),
            ))
        })
    }
}
