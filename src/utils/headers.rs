use pyo3::{
    Bound,
    types::{PyAnyMethods, PyDict},
};

use crate::exceptions::rust_err::NatsrpyResult;

pub trait NatsrpyHeadermapExt: Sized {
    fn from_pydict(pydict: Bound<PyDict>) -> NatsrpyResult<Self>;
}

impl NatsrpyHeadermapExt for async_nats::HeaderMap {
    fn from_pydict(pydict: Bound<PyDict>) -> NatsrpyResult<Self> {
        let mut headermap = Self::new();
        for (name, val) in pydict {
            let rs_name = name.extract::<String>()?;
            if let Ok(parsed_str) = val.extract::<String>() {
                headermap.insert(rs_name, parsed_str);
                continue;
            }
            headermap.insert(rs_name, val.to_string());
        }
        Ok(headermap)
    }
}
