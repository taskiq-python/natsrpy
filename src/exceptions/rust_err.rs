use pyo3::exceptions::{PyStopAsyncIteration, PyTimeoutError, PyTypeError};

use crate::exceptions::py_err::{NatsrpyPublishError, NatsrpySessionError};

pub type NatsrpyResult<T> = Result<T, NatsrpyError>;

#[derive(thiserror::Error, Debug)]
pub enum NatsrpyError {
    #[error(transparent)]
    StdIOError(#[from] std::io::Error),
    #[error("The lock is poisoned")]
    PoisonedLock,
    #[error(transparent)]
    StdParseIntError(#[from] std::num::ParseIntError),
    #[error(transparent)]
    JSONParseError(#[from] serde_json::Error),
    #[error(transparent)]
    UnknownError(#[from] Box<dyn std::error::Error + Send + Sync + 'static>),
    #[error("NATS session error: {0}")]
    SessionError(String),
    #[error("Invalid arguemnt: {0}")]
    InvalidArgument(String),
    #[error("Session is not initialized. Call startup() first.")]
    NotInitialized,
    #[error("The end of stream")]
    AsyncStopIteration,
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
    UnsubscribeError(#[from] async_nats::UnsubscribeError),
    #[error(transparent)]
    JSKVError(#[from] async_nats::jetstream::context::KeyValueError),
    #[error(transparent)]
    JSKVCreateError(#[from] async_nats::jetstream::context::CreateKeyValueError),
    #[error(transparent)]
    JSStreamCreateError(#[from] async_nats::jetstream::context::CreateStreamError),
    #[error(transparent)]
    JSStreamGetError(#[from] async_nats::jetstream::context::GetStreamError),
    #[error(transparent)]
    JSKVUpdateError(#[from] async_nats::jetstream::context::UpdateKeyValueError),
    #[error(transparent)]
    JSPublishError(#[from] async_nats::jetstream::context::PublishError),
    #[error(transparent)]
    JSObjectStoreError(#[from] async_nats::jetstream::context::ObjectStoreError),
    #[error(transparent)]
    KVEntryError(#[from] async_nats::jetstream::kv::EntryError),
    #[error(transparent)]
    KVPutError(#[from] async_nats::jetstream::kv::PutError),
    #[error(transparent)]
    KVUpdateError(#[from] async_nats::jetstream::kv::UpdateError),
    #[error(transparent)]
    KVCreateError(#[from] async_nats::jetstream::kv::CreateError),
    #[error(transparent)]
    KVWatcherError(#[from] async_nats::jetstream::kv::WatcherError),
    #[error(transparent)]
    KVHistoryError(#[from] async_nats::jetstream::kv::HistoryError),
    #[error(transparent)]
    KVStatusError(#[from] async_nats::jetstream::kv::StatusError),
    #[error(transparent)]
    StreamDirectGetError(#[from] async_nats::jetstream::stream::DirectGetError),
    #[error(transparent)]
    StreamInfoError(#[from] async_nats::jetstream::stream::InfoError),
    #[error(transparent)]
    StreamPurgeError(#[from] async_nats::jetstream::stream::PurgeError),
    #[error(transparent)]
    StreamLastRawMessageError(#[from] async_nats::jetstream::stream::LastRawMessageError),
    #[error(transparent)]
    StreamDeleteMessageError(#[from] async_nats::jetstream::stream::DeleteMessageError),
    #[error(transparent)]
    ConsumerError(#[from] async_nats::jetstream::stream::ConsumerError),
    #[error(transparent)]
    PullMessageError(#[from] async_nats::jetstream::consumer::pull::MessagesError),
    #[error(transparent)]
    PullConsumerBatchError(#[from] async_nats::jetstream::consumer::pull::BatchError),
    #[error(transparent)]
    PushConsumerMessageError(#[from] async_nats::jetstream::consumer::push::MessagesError),
    #[error(transparent)]
    ConsumerStreamError(#[from] async_nats::jetstream::consumer::StreamError),
    #[error(transparent)]
    ConsumerUpdateError(#[from] async_nats::jetstream::stream::ConsumerUpdateError),
    #[error(transparent)]
    ObjectStoreGetError(#[from] async_nats::jetstream::object_store::GetError),
    #[error(transparent)]
    ObjectStorePutError(#[from] async_nats::jetstream::object_store::PutError),
    #[error(transparent)]
    ObjectStoreDeleteError(#[from] async_nats::jetstream::object_store::DeleteError),
    #[error(transparent)]
    ObjectStoreSealError(#[from] async_nats::jetstream::object_store::SealError),
    #[error(transparent)]
    ObjectStoreInfoError(#[from] async_nats::jetstream::object_store::InfoError),
    #[error(transparent)]
    ObjectStoreWatchError(#[from] async_nats::jetstream::object_store::WatchError),
    #[error(transparent)]
    ObjectStoreWatcherError(#[from] async_nats::jetstream::object_store::WatcherError),
    #[error(transparent)]
    ObjectStoreAddLinkError(#[from] async_nats::jetstream::object_store::AddLinkError),
    #[error(transparent)]
    ObjectStoreUpdateMetadataError(
        #[from] async_nats::jetstream::object_store::UpdateMetadataError,
    ),
}

impl From<NatsrpyError> for pyo3::PyErr {
    fn from(value: NatsrpyError) -> Self {
        match value {
            NatsrpyError::PublishError(_) => NatsrpyPublishError::new_err(value.to_string()),
            NatsrpyError::AsyncStopIteration => PyStopAsyncIteration::new_err("End of the stream."),
            NatsrpyError::Timeout(_) => PyTimeoutError::new_err(value.to_string()),
            NatsrpyError::PyError(py_err) => py_err,
            NatsrpyError::InvalidArgument(descr) => PyTypeError::new_err(descr),
            _ => NatsrpySessionError::new_err(value.to_string()),
        }
    }
}
