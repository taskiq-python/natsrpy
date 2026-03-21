use std::time::Duration;

use pyo3::{
    FromPyObject,
    types::{PyBytes, PyBytesMethods},
};

use crate::exceptions::rust_err::NatsrpyError;

#[derive(Clone, Debug)]
pub enum SendableValue {
    Bytes(bytes::Bytes),
    String(String),
}

impl<'py> FromPyObject<'_, 'py> for SendableValue {
    type Error = NatsrpyError;

    fn extract(obj: pyo3::Borrowed<'_, 'py, pyo3::PyAny>) -> Result<Self, Self::Error> {
        #[allow(clippy::option_if_let_else)]
        if let Ok(pybytes) = obj.cast::<PyBytes>() {
            Ok(Self::Bytes(bytes::Bytes::copy_from_slice(
                pybytes.as_bytes(),
            )))
        } else if let Ok(pybytes) = obj.extract::<Vec<u8>>() {
            Ok(Self::Bytes(bytes::Bytes::from(pybytes)))
        } else if let Ok(str_data) = obj.extract::<String>() {
            Ok(Self::String(str_data))
        } else {
            Err(NatsrpyError::InvalidArgument(String::from(
                "String or bytes are the only accepted values",
            )))
        }
    }
}

impl From<SendableValue> for bytes::Bytes {
    fn from(value: SendableValue) -> Self {
        match value {
            SendableValue::Bytes(bytes) => bytes,
            SendableValue::String(str) => Self::from(str.into_bytes()),
        }
    }
}

#[derive(Clone, Debug, Copy, PartialEq, PartialOrd)]
pub enum TimeoutValue {
    Duration(Duration),
    FloatSecs(f32),
}

impl From<TimeoutValue> for Duration {
    fn from(value: TimeoutValue) -> Self {
        match value {
            TimeoutValue::Duration(duration) => duration,
            TimeoutValue::FloatSecs(fsecs) => Self::from_secs_f32(fsecs),
        }
    }
}

impl<'py> FromPyObject<'_, 'py> for TimeoutValue {
    type Error = NatsrpyError;

    fn extract(obj: pyo3::Borrowed<'_, 'py, pyo3::PyAny>) -> Result<Self, Self::Error> {
        #[allow(clippy::option_if_let_else)]
        if let Ok(fsec) = obj.extract::<f32>() {
            Ok(Self::FloatSecs(fsec))
        } else if let Ok(duration) = obj.extract::<Duration>() {
            Ok(Self::Duration(duration))
        } else {
            Err(NatsrpyError::InvalidArgument(String::from(
                "As timeouts only float or timedelta are accepted.",
            )))
        }
    }
}
