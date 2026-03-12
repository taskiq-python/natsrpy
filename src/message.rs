use pyo3::{
    Py, Python,
    types::{PyBytes, PyDict},
};

use crate::{exceptions::rust_err::NatsrpyResult, utils::headers::NatsrpyHeadermapExt};

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
    pub fn from_nats_message(py: Python<'_>, message: async_nats::Message) -> NatsrpyResult<Self> {
        let headers = match message.headers {
            Some(headermap) => headermap.to_pydict(py)?,
            None => PyDict::new(py).unbind(),
        };
        Ok(Self {
            subject: message.subject.to_string(),
            reply: message.reply.as_deref().map(ToString::to_string),
            payload: PyBytes::new(py, &message.payload).unbind(),
            headers,
            status: message.status.map(Into::<u16>::into),
            description: message.description,
            length: message.length,
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
}
