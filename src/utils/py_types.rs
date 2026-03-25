use std::time::Duration;

use pyo3::{
    Bound, FromPyObject, PyResult, Python, type_hint_identifier, type_hint_union,
    types::{PyBytes, PyBytesMethods, PyDateTime, PyTzInfo},
};

use crate::exceptions::rust_err::NatsrpyError;

#[derive(Clone, Debug)]
pub enum SendableValue {
    Bytes(bytes::Bytes),
    String(String),
}

impl<'py> FromPyObject<'_, 'py> for SendableValue {
    type Error = NatsrpyError;
    const INPUT_TYPE: pyo3::inspect::PyStaticExpr = type_hint_union!(
        type_hint_identifier!("builtins", "str"),
        type_hint_identifier!("builtins", "bytes"),
        type_hint_identifier!("builtins", "bytearray"),
        type_hint_identifier!("builtins", "memoryview")
    );

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
pub enum TimeValue {
    Duration(Duration),
    FloatSecs(f32),
}

impl From<TimeValue> for Duration {
    fn from(value: TimeValue) -> Self {
        match value {
            TimeValue::Duration(duration) => duration,
            TimeValue::FloatSecs(fsecs) => Self::from_secs_f32(fsecs),
        }
    }
}

impl Default for TimeValue {
    fn default() -> Self {
        Self::Duration(Duration::default())
    }
}

impl<'py> FromPyObject<'_, 'py> for TimeValue {
    type Error = NatsrpyError;

    const INPUT_TYPE: pyo3::inspect::PyStaticExpr = type_hint_union!(
        type_hint_identifier!("builtins", "float"),
        type_hint_identifier!("datetime", "timedelta")
    );

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

pub trait ToPyDate {
    fn to_py_date<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDateTime>>;
}

impl ToPyDate for time::OffsetDateTime {
    fn to_py_date<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDateTime>> {
        let time = self.to_utc();
        let tz_info = PyTzInfo::utc(py)?;
        PyDateTime::new(
            py,
            time.year(),
            time.month().into(),
            time.day(),
            time.hour(),
            time.minute(),
            time.second(),
            time.microsecond(),
            Some(&*tz_info),
        )
    }
}
