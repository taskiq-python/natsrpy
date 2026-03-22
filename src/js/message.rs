use pyo3::{
    Bound, Py, PyAny, Python,
    types::{PyBytes, PyDict},
};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::{natsrpy_future, py_types::TimeValue},
};

#[pyo3::pyclass]
pub struct JetStreamMessage {
    message: crate::message::Message,
    acker: Arc<RwLock<async_nats::jetstream::message::Acker>>,
}

impl TryFrom<async_nats::jetstream::Message> for JetStreamMessage {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::jetstream::Message) -> Result<Self, Self::Error> {
        let (message, acker) = value.split();
        Ok(Self {
            message: message.try_into()?,
            acker: Arc::new(RwLock::new(acker)),
        })
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
    #[must_use]
    pub const fn subject(&self) -> &str {
        self.message.subject.as_str()
    }
    #[getter]
    #[must_use]
    pub const fn reply(&self) -> &Option<String> {
        &self.message.reply
    }
    #[getter]
    #[must_use]
    pub const fn payload(&self) -> &Py<PyBytes> {
        &self.message.payload
    }
    #[getter]
    pub const fn headers(&mut self) -> &Py<PyDict> {
        &self.message.headers
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

    #[must_use]
    pub fn __repr__(&self) -> String {
        self.message.__repr__()
    }
}
