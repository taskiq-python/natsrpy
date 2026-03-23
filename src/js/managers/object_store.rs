use std::sync::Arc;

use pyo3::{Bound, PyAny, Python};
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::NatsrpyResult,
    js::object_store::{ObjectStore, ObjectStoreConfig},
    utils::natsrpy_future,
};

#[pyo3::pyclass]
pub struct ObjectStoreManager {
    ctx: Arc<RwLock<async_nats::jetstream::Context>>,
}

impl ObjectStoreManager {
    pub const fn new(ctx: Arc<RwLock<async_nats::jetstream::Context>>) -> Self {
        Self { ctx }
    }
}

#[pyo3::pymethods]
impl ObjectStoreManager {
    pub fn get<'py>(&self, py: Python<'py>, bucket: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(ObjectStore::new(
                ctx_guard.read().await.get_object_store(bucket).await?,
            ))
        })
    }

    pub fn create<'py>(
        &self,
        py: Python<'py>,
        config: ObjectStoreConfig,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.ctx.clone();
        natsrpy_future(py, async move {
            Ok(ObjectStore::new(
                ctx_guard
                    .read()
                    .await
                    .create_object_store(config.into())
                    .await?,
            ))
        })
    }

    pub fn delete<'py>(&self, py: Python<'py>, bucket: String) -> NatsrpyResult<Bound<'py, PyAny>> {
        let ctx_guard = self.ctx.clone();
        natsrpy_future(py, async move {
            ctx_guard.read().await.delete_object_store(bucket).await?;
            Ok(())
        })
    }
}
