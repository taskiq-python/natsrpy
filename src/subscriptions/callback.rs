use std::sync::Arc;

use futures_util::StreamExt;
use pyo3::{Bound, Py, PyAny, Python};

use crate::{
    exceptions::rust_err::NatsrpyResult,
    utils::{async_event::AsyncEvent, natsrpy_future},
};

enum UnsubscribeCommand {
    Unsubscribe,
    UnsubscribeAfter(u64),
    Drain,
}

#[pyo3::pyclass(from_py_object)]
#[derive(Clone)]
pub struct CallbackSubscription {
    unsub_sender: Option<tokio::sync::mpsc::Sender<UnsubscribeCommand>>,
    reading_task: tokio::task::AbortHandle,
    end_notify: AsyncEvent,
}

async fn process_message(message: async_nats::message::Message, py_callback: Arc<Py<PyAny>>) {
    let task = async || -> NatsrpyResult<()> {
        log::debug!("Received message: {:?}. Processing ...", &message);
        let awaitable = Python::attach(|gil| -> NatsrpyResult<_> {
            let message = crate::message::Message::from_nats_message(gil, &message)?;
            let res = py_callback.call1(gil, (message,))?;
            let rust_task = pyo3_async_runtimes::tokio::into_future(res.into_bound(gil))?;
            Ok(rust_task)
        })?;
        awaitable.await?;
        log::debug!("Python callback successfully awaited.");
        Ok(())
    };
    if let Err(err) = task().await {
        log::error!("Cannot process message {message:?}. Error: {err}");
    }
}

async fn start_py_sub(
    mut sub: async_nats::Subscriber,
    py_callback: Arc<Py<PyAny>>,
    locals: pyo3_async_runtimes::TaskLocals,
    mut unsub_receiver: tokio::sync::mpsc::Receiver<UnsubscribeCommand>,
    end_event: AsyncEvent,
) {
    // Required to wait for completion of processing tasks.
    //
    // This will ensure that end_event is only set after
    // processing of all messages is finished.
    let mut tasks = tokio::task::JoinSet::new();
    loop {
        tokio::select! {
            msg = sub.next() => {
                match msg {
                    Some(message) => {
                        let py_cb = py_callback.clone();
                        tasks.spawn(pyo3_async_runtimes::tokio::scope(
                            locals.clone(),
                            process_message(message, py_cb),
                        ));
                    }
                    None => break,
                }
            }
            cmd = unsub_receiver.recv() => {
                match cmd {
                    Some(UnsubscribeCommand::Unsubscribe) => {
                        sub.unsubscribe().await.ok();
                    }
                    Some(UnsubscribeCommand::UnsubscribeAfter(limit)) => {
                        sub.unsubscribe_after(limit).await.ok();
                    }
                    Some(UnsubscribeCommand::Drain) => {
                        sub.drain().await.ok();
                    }
                    None => break,
                }
            }
        }
    }
    tasks.join_all().await;
    end_event.set();
}

impl CallbackSubscription {
    pub fn new(sub: async_nats::Subscriber, callback: Py<PyAny>) -> NatsrpyResult<Self> {
        let (unsub_tx, unsub_rx) = tokio::sync::mpsc::channel(1);
        let task_locals = Python::attach(pyo3_async_runtimes::tokio::get_current_locals)?;
        let callback = Arc::new(callback);
        let event = AsyncEvent::default();
        let task_handle = tokio::task::spawn(pyo3_async_runtimes::tokio::scope(
            task_locals.clone(),
            start_py_sub(sub, callback, task_locals, unsub_rx, event.clone()),
        ))
        .abort_handle();
        Ok(Self {
            unsub_sender: Some(unsub_tx),
            reading_task: task_handle,
            end_notify: event,
        })
    }
}

#[pyo3::pymethods]
impl CallbackSubscription {
    #[pyo3(signature=(limit=None))]
    pub fn unsubscribe<'py>(
        &self,
        py: Python<'py>,
        limit: Option<u64>,
    ) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(sender) = self.unsub_sender.clone() else {
            unreachable!("Subscription used after del")
        };
        natsrpy_future(py, async move {
            let cmd = limit.map_or(UnsubscribeCommand::Unsubscribe, |n| {
                UnsubscribeCommand::UnsubscribeAfter(n)
            });
            sender.send(cmd).await.map_err(|_| {
                crate::exceptions::rust_err::NatsrpyError::SessionError(
                    "Subscription already closed".to_string(),
                )
            })?;
            Ok(())
        })
    }

    pub fn drain<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let Some(sender) = self.unsub_sender.clone() else {
            unreachable!("Subscription used after del")
        };
        natsrpy_future(py, async move {
            sender.send(UnsubscribeCommand::Drain).await.map_err(|_| {
                crate::exceptions::rust_err::NatsrpyError::SessionError(
                    "Subscription already closed".to_string(),
                )
            })?;
            Ok(())
        })
    }

    pub fn wait<'py>(&self, py: Python<'py>) -> NatsrpyResult<Bound<'py, PyAny>> {
        let event = self.end_notify.clone();
        natsrpy_future(py, async move {
            event.wait().await;
            Ok(())
        })
    }
}

impl Drop for CallbackSubscription {
    fn drop(&mut self) {
        // Drop the sender to signal the reading task to stop,
        // then abort the task. Both operations are synchronous
        // and don't require an async runtime context.
        self.unsub_sender = None;
        self.reading_task.abort();
    }
}
