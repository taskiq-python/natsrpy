use std::ops::Deref;

use crate::exceptions::rust_err::NatsrpyError;
use crate::exceptions::rust_err::NatsrpyResult;
use pyo3::Bound;
use pyo3::pyclass;
use pyo3::pymethods;

#[pyclass(from_py_object)]
#[derive(Clone, Copy, Default)]
pub enum StorageType {
    #[default]
    FILE,
    MEMORY,
}

impl From<StorageType> for async_nats::jetstream::stream::StorageType {
    fn from(value: StorageType) -> Self {
        match value {
            StorageType::FILE => Self::File,
            StorageType::MEMORY => Self::Memory,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct Republish {
    pub source: String,
    pub destination: String,
    pub headers_only: bool,
}

impl From<Republish> for async_nats::jetstream::stream::Republish {
    fn from(value: Republish) -> Self {
        Self {
            source: value.source.clone(),
            destination: value.destination.clone(),
            headers_only: value.headers_only,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct External {
    pub api_prefix: String,
    pub delivery_prefix: Option<String>,
}

#[pymethods]
impl External {
    #[new]
    #[pyo3(signature = (api_prefix, delivery_prefix=None))]
    #[must_use] 
    pub const fn __new__(api_prefix: String, delivery_prefix: Option<String>) -> Self {
        Self {
            api_prefix,
            delivery_prefix,
        }
    }
}

impl From<&External> for async_nats::jetstream::stream::External {
    fn from(value: &External) -> Self {
        Self {
            api_prefix: value.api_prefix.clone(),
            delivery_prefix: value.delivery_prefix.clone(),
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct SubjectTransform {
    pub source: String,
    pub destination: String,
}

impl From<SubjectTransform> for async_nats::jetstream::stream::SubjectTransform {
    fn from(value: SubjectTransform) -> Self {
        Self {
            source: value.source,
            destination: value.destination,
        }
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct Source {
    pub name: String,
    pub filter_subject: Option<String>,
    pub external: Option<External>,
    pub start_sequence: Option<u64>,
    pub start_time: Option<i64>,
    pub domain: Option<String>,
    pub subject_transforms: Vec<SubjectTransform>,
}

impl TryFrom<Source> for async_nats::jetstream::stream::Source {
    type Error = NatsrpyError;

    fn try_from(value: Source) -> Result<Self, Self::Error> {
        Ok(Self {
            name: value.name.clone(),
            filter_subject: value.filter_subject.clone(),
            external: value.external.as_ref().map(std::convert::Into::into),
            start_sequence: value.start_sequence,
            start_time: value
                .start_time
                .map(time::OffsetDateTime::from_unix_timestamp)
                .transpose()?,
            domain: value.domain.clone(),
            subject_transforms: value
                .subject_transforms
                
                .into_iter()
                .map(std::convert::Into::into)
                .collect(),
        })
    }
}

#[pymethods]
impl Source {
    #[new]
    #[pyo3(signature = (
        name,
        filter_subject=None,
        external=None,
        start_sequence = None,
        start_time=None,
        domain=None,
        subject_transforms = vec![]
    ))]
    pub fn __new__(
        name: String,
        filter_subject: Option<String>,
        external: Option<Bound<'_, External>>,
        start_sequence: Option<u64>,
        start_time: Option<i64>,
        domain: Option<String>,
        subject_transforms: Vec<Bound<'_, SubjectTransform>>,
    ) -> NatsrpyResult<Self> {
        Ok(Self {
            name,
            domain,
            start_time,
            start_sequence,
            filter_subject,
            subject_transforms: subject_transforms
                .into_iter()
                .map(|val| val.borrow().deref().clone())
                .collect(),
            external: external.map(|e| e.borrow().deref().clone()),
        })
    }
}

#[pyclass(from_py_object, get_all, set_all)]
#[derive(Clone)]
pub struct Placement {
    pub cluster: Option<String>,
    pub tags: Vec<String>,
}

#[pymethods]
impl Placement {
    #[new]
    #[pyo3(signature=(cluster=None, tags=None))]
    #[must_use] 
    pub fn __new__(cluster: Option<String>, tags: Option<Vec<String>>) -> Self {
        Self {
            cluster,
            tags: tags.unwrap_or_default(),
        }
    }
}

impl From<Placement> for async_nats::jetstream::stream::Placement {
    fn from(value: Placement) -> Self {
        Self {
            cluster: value.cluster,
            tags: value.tags,
        }
    }
}

#[pyo3::pymodule(submodule, name = "stream")]
pub mod pymod {
    #[pymodule_export]
    pub use super::{External, Placement, Republish, Source, StorageType, SubjectTransform};
}
