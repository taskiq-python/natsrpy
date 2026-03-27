use std::sync::Arc;

use pyo3::{Bound, PyAny, Python};

use crate::{
    exceptions::rust_err::NatsrpyResult,
    js::kv::{KVConfig, KeyValue},
    utils::natsrpy_future,
};

#[pyo3::pyclass]
pub struct KVManager {
    ctx: Arc<async_nats::jetstream::Context>,
}

impl KVManager {
    #[must_use]
    pub const fn new(ctx: Arc<async_nats::jetstream::Context>) -> Self {
        Self { ctx }
    }
}

#[pyo3::pymethods]
impl KVManager {
    pub fn create<'py>(
        &self,
        py: Python<'py>,
        config: KVConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(KeyValue::new(
                client.create_key_value(config.try_into()?).await?,
            ))
        })
    }

    pub fn create_or_update<'py>(
        &self,
        py: Python<'py>,
        config: KVConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(KeyValue::new(
                client
                    .create_or_update_key_value(config.try_into()?)
                    .await?,
            ))
        })
    }

    pub fn get<'py>(&self, py: Python<'py>, bucket: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(KeyValue::new(client.get_key_value(bucket).await?))
        })
    }

    pub fn delete<'py>(&self, py: Python<'py>, bucket: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(client.delete_key_value(bucket).await?.success)
        })
    }

    pub fn update<'py>(
        &self,
        py: Python<'py>,
        config: KVConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let client = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(KeyValue::new(
                client.update_key_value(config.try_into()?).await?,
            ))
        })
    }
}
