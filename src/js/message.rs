use pyo3::{
    Bound, Py, PyAny, Python,
    types::{PyBytes, PyDateTime, PyDict},
};
use std::sync::Arc;

use crate::{
    exceptions::rust_err::{NatsrpyError, NatsrpyResult},
    utils::{
        natsrpy_future,
        py_types::{TimeValue, ToPyDate},
    },
};

#[derive(Debug, Clone)]
pub struct JSInfo {
    pub domain: Option<String>,
    pub acc_hash: Option<String>,
    pub stream: String,
    pub consumer: String,
    pub stream_sequence: u64,
    pub consumer_sequence: u64,
    pub delivered: i64,
    pub pending: u64,
    pub published: time::OffsetDateTime,
    pub token: Option<String>,
}

impl From<async_nats::jetstream::message::Info<'_>> for JSInfo {
    fn from(value: async_nats::jetstream::message::Info) -> Self {
        Self {
            domain: value.domain.map(ToString::to_string),
            acc_hash: value.acc_hash.map(ToString::to_string),
            stream: value.stream.to_string(),
            consumer: value.consumer.to_string(),
            stream_sequence: value.stream_sequence,
            consumer_sequence: value.consumer_sequence,
            delivered: value.delivered,
            pending: value.pending,
            published: value.published,
            token: value.token.map(ToString::to_string),
        }
    }
}

#[pyo3::pyclass]
pub struct JetStreamMessage {
    message: crate::message::Message,
    info: JSInfo,
    acker: Arc<async_nats::jetstream::message::Acker>,
}

impl TryFrom<async_nats::jetstream::Message> for JetStreamMessage {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::jetstream::Message) -> Result<Self, Self::Error> {
        let js_info = JSInfo::from(value.info()?);
        let (message, acker) = value.split();
        Ok(Self {
            message: message.try_into()?,
            info: js_info,
            acker: Arc::new(acker),
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
        let acker = self.acker.clone();
        natsrpy_future(py, async move {
            if double {
                acker.double_ack_with(kind).await?;
            } else {
                acker.ack_with(kind).await?;
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
    pub const fn length(&self) -> usize {
        self.message.length
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

    #[getter]
    pub const fn domain(&mut self) -> &Option<String> {
        &self.info.domain
    }

    #[getter]
    #[must_use]
    pub const fn acc_hash(&self) -> &Option<String> {
        &self.info.acc_hash
    }
    #[getter]
    #[must_use]
    pub const fn stream(&self) -> &str {
        self.info.stream.as_str()
    }
    #[getter]
    #[must_use]
    pub const fn consumer(&self) -> &str {
        self.info.consumer.as_str()
    }
    #[getter]
    #[must_use]
    pub const fn stream_sequence(&self) -> u64 {
        self.info.stream_sequence
    }
    #[getter]
    #[must_use]
    pub const fn consumer_sequence(&self) -> u64 {
        self.info.consumer_sequence
    }
    #[getter]
    #[must_use]
    pub const fn delivered(&self) -> i64 {
        self.info.delivered
    }
    #[getter]
    #[must_use]
    pub const fn pending(&self) -> u64 {
        self.info.pending
    }
    #[getter]
    pub fn published<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyDateTime>> {
        Ok(self.info.published.to_py_date(py)?)
    }

    #[getter]
    #[must_use]
    pub const fn token(&self) -> &Option<String> {
        &self.info.token
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
    #[must_use]
    pub const fn __len__(&self) -> usize {
        self.message.length
    }
}
