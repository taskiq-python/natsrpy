use pyo3::{
    Bound, Py, Python,
    types::{PyAnyMethods, PyDict},
};

use crate::exceptions::rust_err::NatsrpyResult;

pub trait NatsrpyHeadermapExt: Sized {
    fn from_pydict(pydict: Bound<PyDict>) -> NatsrpyResult<Self>;
    fn to_pydict(&self, py: Python) -> NatsrpyResult<Py<PyDict>>;
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
            if let Ok(parsed_list) = val.extract::<Vec<String>>() {
                for inner in parsed_list {
                    headermap.append(rs_name.as_str(), inner);
                }
                continue;
            }
            headermap.insert(rs_name, val.to_string());
        }
        Ok(headermap)
    }

    fn to_pydict(&self, py: Python) -> NatsrpyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        for (header_name, header_val) in self.iter() {
            let py_val = header_val
                .iter()
                .map(std::string::ToString::to_string)
                .collect::<Vec<_>>();
            if py_val.is_empty() {
                continue;
            }
            if py_val.len() == 1 {
                dict.set_item(header_name.to_string(), py_val.first())?;
                continue;
            }
            dict.set_item(header_name.to_string(), py_val)?;
        }
        Ok(dict.unbind())
    }
}
