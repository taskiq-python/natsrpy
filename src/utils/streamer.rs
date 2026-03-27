use std::{sync::Arc, task::Poll};

use futures_util::StreamExt;
use tokio::sync::Mutex;

#[derive(Clone, Debug)]
pub struct Streamer<T> {
    messages: Arc<Mutex<tokio::sync::mpsc::Receiver<T>>>,
    abort_handle: tokio::task::AbortHandle,
}

async fn task_pooler<T>(
    mut stream: impl futures_util::Stream<Item = T> + std::marker::Unpin + Send + 'static,
    channel: tokio::sync::mpsc::Sender<T>,
) {
    while let Some(msg) = stream.next().await {
        if let Err(err) = channel.send(msg).await {
            log::error!("Cannot send updates to streaming channel. Cause: {err}.");
        }
    }
}

impl<T: Send + 'static> Streamer<T> {
    pub fn new(
        stream: impl futures_util::Stream<Item = T> + std::marker::Unpin + Send + 'static,
    ) -> Self {
        let (tx, rx) = tokio::sync::mpsc::channel(128);
        let task = tokio::task::spawn(task_pooler(stream, tx));
        Self {
            messages: Arc::new(Mutex::new(rx)),
            abort_handle: task.abort_handle(),
        }
    }
}

impl<T> Streamer<T> {
    pub async fn close(&mut self) {
        self.abort_handle.abort();
        self.messages.lock().await.close();
    }
}

impl<T> futures_util::Stream for Streamer<T> {
    type Item = T;

    fn poll_next(
        self: std::pin::Pin<&mut Self>,
        cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Option<Self::Item>> {
        let mutex = std::pin::pin!(self.messages.lock());
        let Poll::Ready(mut lock) = mutex.poll(cx) else {
            return Poll::Pending;
        };
        lock.poll_recv(cx)
    }
}

impl<T> Drop for Streamer<T> {
    fn drop(&mut self) {
        pyo3_async_runtimes::tokio::get_runtime().block_on(async move {
            self.close().await;
        });
    }
}
