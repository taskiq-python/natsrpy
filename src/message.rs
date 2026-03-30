use pyo3::{
    Py, Python,
    types::{PyBytes, PyDict},
};

use crate::{exceptions::rust_err::NatsrpyError, utils::headers::NatsrpyHeadermapExt};

#[pyo3::pyclass(get_all, set_all)]
#[derive(Debug)]
pub struct Message {
    pub subject: String,
    pub reply: Option<String>,
    pub payload: Py<PyBytes>,
    pub headers: Py<PyDict>,
    pub status: Option<u16>,
    pub description: Option<String>,
    pub length: usize,
}

impl Message {
    /// Convert from an `async_nats::Message` using an already-held GIL token.
    /// This avoids a redundant `Python::attach` call when the caller already has the GIL.
    pub fn from_nats_message(
        gil: Python<'_>,
        value: &async_nats::Message,
    ) -> Result<Self, NatsrpyError> {
        let headers = match &value.headers {
            Some(headermap) => headermap.to_pydict(gil)?.unbind(),
            None => PyDict::new(gil).unbind(),
        };
        Ok(Self {
            subject: value.subject.to_string(),
            reply: value.reply.as_deref().map(ToString::to_string),
            payload: PyBytes::new(gil, &value.payload).unbind(),
            headers,
            status: value.status.map(Into::<u16>::into),
            description: value.description.clone(),
            length: value.length,
        })
    }
}

impl TryFrom<&async_nats::Message> for Message {
    type Error = NatsrpyError;

    fn try_from(value: &async_nats::Message) -> Result<Self, Self::Error> {
        Python::attach(move |gil| Self::from_nats_message(gil, value))
    }
}

impl TryFrom<async_nats::Message> for Message {
    type Error = NatsrpyError;

    fn try_from(value: async_nats::Message) -> Result<Self, Self::Error> {
        Python::attach(move |gil| {
            let headers = match &value.headers {
                Some(headermap) => headermap.to_pydict(gil)?.unbind(),
                None => PyDict::new(gil).unbind(),
            };
            Ok(Self {
                subject: value.subject.into_string(),
                reply: value.reply.map(async_nats::Subject::into_string),
                payload: PyBytes::new(gil, &value.payload).unbind(),
                headers,
                status: value.status.map(Into::<u16>::into),
                description: value.description,
                length: value.length,
            })
        })
    }
}

#[pyo3::pymethods]
impl Message {
    #[must_use]
    pub fn __repr__(&self) -> String {
        format!(
            r#"Message<subject="{subject}", reply={reply:?}, payload={payload}, headers={headers}, description={description:?}, length={len}>"#,
            subject = self.subject,
            reply = self.reply,
            payload = self.payload,
            headers = self.headers,
            description = self.description,
            len = self.length,
        )
    }
    #[must_use]
    pub const fn __len__(&self) -> usize {
        self.length
    }
}
