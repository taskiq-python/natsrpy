use std::sync::Arc;

use crate::{
    exceptions::rust_err::NatsrpyError,
    js::counters::{Counters, CountersConfig},
};
use pyo3::{Bound, PyAny, Python};

use crate::{exceptions::rust_err::NatsrpyResult, utils::natsrpy_future};

#[pyo3::pyclass]
pub struct CountersManager {
    ctx: Arc<async_nats::jetstream::Context>,
}

impl CountersManager {
    #[must_use]
    pub const fn new(ctx: Arc<async_nats::jetstream::Context>) -> Self {
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
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(Counters::new(
                client
                    .create_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                    .await?,
                client,
            ))
        })
    }

    pub fn create_or_update<'py>(
        &self,
        py: Python<'py>,
        config: CountersConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = client
                .create_or_update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Counters::new(
                client.get_stream(info.config.name).await?,
                client,
            ))
        })
    }

    pub fn get<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            let stream = client.get_stream(&name).await?;
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
            Ok(Counters::new(stream, client))
        })
    }

    pub fn delete<'py>(&self, py: Python<'py>, name: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(
            py,
            async move { Ok(client.delete_stream(name).await?.success) },
        )
    }

    pub fn update<'py>(
        &self,
        py: Python<'py>,
        config: CountersConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            let info = client
                .update_stream(async_nats::jetstream::stream::Config::try_from(config)?)
                .await?;
            Ok(Counters::new(
                client.get_stream(info.config.name).await?,
                client,
            ))
        })
    }
}
