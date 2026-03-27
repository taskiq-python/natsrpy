use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, PyAny, PyRef, Python};

use crate::exceptions::rust_err::{NatsrpyError, NatsrpyResult};
use crate::utils::futures::natsrpy_future_with_timeout;
use crate::utils::natsrpy_future;
use crate::utils::py_types::TimeValue;

enum UnsubscribeCommand {
    Unsubscribe,
    UnsubscribeAfter(u64),
    Drain,
}

/// Background task that owns the subscriber and forwards messages
/// to an mpsc channel. Listens for unsubscribe commands on a separate channel.
async fn sub_forwarder(
    mut sub: async_nats::Subscriber,
    msg_tx: tokio::sync::mpsc::Sender<async_nats::Message>,
    mut unsub_rx: tokio::sync::mpsc::Receiver<UnsubscribeCommand>,
) {
    loop {
        tokio::select! {
            msg = sub.next() => {
                match msg {
                    Some(message) => {
                        if msg_tx.send(message).await.is_err() {
                            // Receiver dropped, stop forwarding.
                            break;
                        }
                    }
                    None => break,
                }
            }
            cmd = unsub_rx.recv() => {
                match cmd {
                    Some(UnsubscribeCommand::Unsubscribe) => {
                        sub.unsubscribe().await.ok();
                        break;
                    }
                    Some(UnsubscribeCommand::UnsubscribeAfter(limit)) => {
                        sub.unsubscribe_after(limit).await.ok();
                        // Don't break — continue receiving up to `limit` messages.
                    }
                    Some(UnsubscribeCommand::Drain) => {
                        sub.drain().await.ok();
                        break;
                    }
                    None => break,
                }
            }
        }
    }
}

#[pyo3::pyclass]
pub struct IteratorSubscription {
    msg_rx: Arc<tokio::sync::Mutex<tokio::sync::mpsc::Receiver<async_nats::Message>>>,
    unsub_tx: Option<tokio::sync::mpsc::Sender<UnsubscribeCommand>>,
    task_handle: tokio::task::AbortHandle,
}

impl IteratorSubscription {
    #[must_use]
    pub fn new(sub: async_nats::Subscriber) -> Self {
        let (msg_tx, msg_rx) = tokio::sync::mpsc::channel(128);
        let (unsub_tx, unsub_rx) = tokio::sync::mpsc::channel(1);
        let task_handle = tokio::task::spawn(sub_forwarder(sub, msg_tx, unsub_rx)).abort_handle();
        Self {
            msg_rx: Arc::new(tokio::sync::Mutex::new(msg_rx)),
            unsub_tx: Some(unsub_tx),
            task_handle,
        }
    }
}

#[pyo3::pymethods]
impl IteratorSubscription {
    #[must_use]
    pub const fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    #[pyo3(signature=(timeout=None))]
    pub fn next<'py>(
        &self,
        py: Python<'py>,
        timeout: Option<TimeValue>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let msg_rx = self.msg_rx.clone();
        natsrpy_future_with_timeout(py, timeout, async move {
            let mut rx = msg_rx.lock().await;
            rx.recv().await.map_or_else(
                || Err(NatsrpyError::AsyncStopIteration),
                crate::message::Message::try_from,
            )
        })
    }

    pub fn __anext__<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        self.next(py, None)
    }

    #[pyo3(signature=(limit=None))]
    pub fn unsubscribe<'py>(
        &self,
        py: Python<'py>,
        limit: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(sender) = self.unsub_tx.clone() else {
            unreachable!("Subscription used after del")
        };
        natsrpy_future(py, async move {
            let cmd = limit.map_or(UnsubscribeCommand::Unsubscribe, |n| {
                UnsubscribeCommand::UnsubscribeAfter(n)
            });
            sender.send(cmd).await.map_err(|_| {
                NatsrpyError::SessionError("Subscription already closed".to_string())
            })?;
            Ok(())
        })
    }

    pub fn drain<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(sender) = self.unsub_tx.clone() else {
            unreachable!("Subscription used after del")
        };
        natsrpy_future(py, async move {
            sender.send(UnsubscribeCommand::Drain).await.map_err(|_| {
                NatsrpyError::SessionError("Subscription already closed".to_string())
            })?;
            Ok(())
        })
    }
}

impl Drop for IteratorSubscription {
    fn drop(&mut self) {
        // Drop the sender to signal the forwarder task to stop,
        // then abort the task. Both operations are synchronous
        // and don't require an async runtime context.
        self.unsub_tx = None;
        self.task_handle.abort();
    }
}
