use pyo3::{Bound, Py, PyAny, Python, types::PyDict};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::NatsrpyResult,
    utils::{headers::NatsrpyHeadermapExt, natsrpy_future, py_types::TimeValue},
};

#[pyo3::pyclass]
pub struct JetStreamMessage {
    message: async_nats::Message,
    headers: Option<Py<PyDict>>,
    acker: Arc<RwLock<async_nats::jetstream::message::Acker>>,
}

impl From<async_nats::jetstream::Message> for JetStreamMessage {
    fn from(value: async_nats::jetstream::Message) -> Self {
        let (message, acker) = value.split();
        Self {
            message,
            headers: None,
            acker: Arc::new(RwLock::new(acker)),
        }
    }
}

impl JetStreamMessage {
    pub fn inner_ack<'py>(
        &self,
        py: Python<'py>,
        kind: async_nats::jetstream::message::AckKind,
        double: bool,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let acker_guard = self.acker.clone();
        natsrpy_future(py, async move {
            if double {
                acker_guard.read().await.double_ack_with(kind).await?;
            } else {
                acker_guard.read().await.ack_with(kind).await?;
            }
            Ok(())
        })
    }
}

#[pyo3::pymethods]
impl JetStreamMessage {
    #[getter]
    pub fn subject(&self) -> &str {
        self.message.subject.as_str()
    }
    #[getter]
    pub fn reply(&self) -> Option<&str> {
        self.message.reply.as_ref().map(async_nats::Subject::as_str)
    }
    #[getter]
    pub fn payload(&self) -> &[u8] {
        &self.message.payload
    }
    #[getter]
    pub fn headers(&mut self, py: Python<'_>) -> NatsrpyResult<Py<PyDict>> {
        if let Some(headers) = &self.headers {
            Ok(headers.clone_ref(py))
        } else {
            let headermap = self.message.headers.clone().unwrap_or_default();
            let headers = headermap.to_pydict(py)?.unbind();
            self.headers = Some(headers.clone_ref(py));
            Ok(headers)
        }
    }

    #[pyo3(signature=(double=false))]
    pub fn ack<'py>(&self, py: Python<'py>, double: bool) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.inner_ack(py, async_nats::jetstream::message::AckKind::Ack, double)
    }

    #[pyo3(signature=(delay=None, double=false))]
    pub fn nack<'py>(
        &self,
        py: Python<'py>,
        delay: Option<TimeValue>,
        double: bool,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.inner_ack(
            py,
            async_nats::jetstream::message::AckKind::Nak(delay.map(Into::into)),
            double,
        )
    }

    #[pyo3(signature=(double=false))]
    pub fn progress<'py>(&self, py: Python<'py>, double: bool) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.inner_ack(
            py,
            async_nats::jetstream::message::AckKind::Progress,
            double,
        )
    }

    #[pyo3(signature=(double=false))]
    pub fn next<'py>(&self, py: Python<'py>, double: bool) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.inner_ack(py, async_nats::jetstream::message::AckKind::Next, double)
    }

    #[pyo3(signature=(double=false))]
    pub fn term<'py>(&self, py: Python<'py>, double: bool) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.inner_ack(py, async_nats::jetstream::message::AckKind::Term, double)
    }
}
