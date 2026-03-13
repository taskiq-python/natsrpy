use pyo3::exceptions::PyTypeError;

use crate::exceptions::py_err::{NatsrpyPublishError, NatsrpySessionError};

pub type NatsrpyResult<T> = Result<T, NatsrpyError>;

#[derive(thiserror::Error, Debug)]
pub enum NatsrpyError {
    #[error("NATS session error: {0}")]
    SessionError(String),
    #[error("Invalid arguemnt: {0}")]
    InvalidArgument(String),
    #[error("Session is not initialized. Call startup() first.")]
    NotInitialized,
    #[error("Connection is closed or lost.")]
    Disconnected,
    #[error(transparent)]
    TimeRangeError(#[from] time::error::ComponentRange),
    #[error("Cannot extract python type: {0}")]
    ExtractError(String),
    #[error(transparent)]
    Timeout(#[from] tokio::time::error::Elapsed),
    #[error(transparent)]
    JoinError(#[from] tokio::task::JoinError),
    #[error(transparent)]
    PyError(#[from] pyo3::PyErr),
    #[error(transparent)]
    ConnectError(#[from] async_nats::ConnectError),
    #[error(transparent)]
    PublishError(#[from] async_nats::PublishError),
    #[error(transparent)]
    RequestError(#[from] async_nats::RequestError),
    #[error(transparent)]
    DrainError(#[from] async_nats::client::DrainError),
    #[error(transparent)]
    FlusError(#[from] async_nats::client::FlushError),
    #[error(transparent)]
    SubscribeError(#[from] async_nats::SubscribeError),
    #[error(transparent)]
    KeyValueError(#[from] async_nats::jetstream::context::KeyValueError),
    #[error(transparent)]
    CreateKeyValueError(#[from] async_nats::jetstream::context::CreateKeyValueError),
    #[error(transparent)]
    KVEntryError(#[from] async_nats::jetstream::kv::EntryError),
    #[error(transparent)]
    KVPutError(#[from] async_nats::jetstream::kv::PutError),
    #[error(transparent)]
    KVUpdateError(#[from] async_nats::jetstream::context::UpdateKeyValueError),
    #[error(transparent)]
    DeleteError(#[from] async_nats::jetstream::kv::DeleteError),
    #[error(transparent)]
    CreateStreamError(#[from] async_nats::jetstream::context::CreateStreamError),
    #[error(transparent)]
    GetStreamError(#[from] async_nats::jetstream::context::GetStreamError),
    #[error(transparent)]
    StreamDirectGetError(#[from] async_nats::jetstream::stream::DirectGetError),
}

impl From<NatsrpyError> for pyo3::PyErr {
    fn from(value: NatsrpyError) -> Self {
        match value {
            NatsrpyError::PublishError(_) => NatsrpyPublishError::new_err(value.to_string()),
            NatsrpyError::PyError(py_err) => py_err,
            NatsrpyError::InvalidArgument(descr) => PyTypeError::new_err(descr),
            _ => NatsrpySessionError::new_err(value.to_string()),
        }
    }
}
