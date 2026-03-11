use pyo3::{
    Py, Python,
    types::{PyAnyMethods, PyBytes, PyDict},
};

use crate::exceptions::rust_err::NatsrpyResult;

#[pyo3::pyclass(get_all, set_all)]
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
    pub fn from_nats_message<'py>(
        py: Python<'py>,
        message: async_nats::Message,
    ) -> NatsrpyResult<Self> {
        let headers = PyDict::new(py);
        if let Some(headermap) = message.headers {
            for (header_name, header_val) in headermap.iter() {
                let py_val = header_val
                    .iter()
                    .map(|val| val.to_string())
                    .collect::<Vec<_>>();
                if py_val.len() == 1 {
                    headers.set_item(header_name.to_string(), py_val.first())?;
                    continue;
                } else {
                    headers.set_item(header_name.to_string(), py_val)?;
                }
            }
        }
        Ok(Self {
            subject: message.subject.to_string(),
            reply: message.reply.as_deref().map(ToString::to_string),
            payload: PyBytes::new(py, &message.payload).unbind(),
            headers: headers.unbind(),
            status: message.status.map(Into::<u16>::into),
            description: message.description,
            length: message.length,
        })
    }
}

#[pyo3::pymethods]
impl Message {
    pub fn __repr__(&self) -> String {
        self.to_string()
    }
}

impl ToString for Message {
    fn to_string(&self) -> String {
        format!(
            r#"Message<subject="{subject}", reply={reply}, payload={payload}, headers={headers}, description={description}, length={len}>"#,
            subject = self.subject,
            reply = format!("{:?}", self.reply),
            payload = self.payload.to_string(),
            headers = self.headers.to_string(),
            description = format!("{:?}", self.description),
            len = self.length,
        )
    }
}
