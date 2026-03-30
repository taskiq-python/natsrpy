use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};

/// Async event.
///
/// This small sync primitive
/// has the same semantics as asyncio.Event from python.
///
/// It's used to wait for an event to occur, and all
/// the following wait calls will succeed until the event is cleared again.
#[derive(Debug, Clone, Default)]
pub struct AsyncEvent {
    is_set: Arc<AtomicBool>,
    notify: Arc<tokio::sync::Notify>,
}

impl AsyncEvent {
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Wait for the event to be set.
    /// If the event is already set, this will return immediately.
    pub async fn wait(&self) {
        loop {
            if self.is_set.load(Ordering::Acquire) {
                return;
            }
            self.notify.notified().await;
        }
    }

    /// Set the event, allowing all waiting tasks to proceed.
    pub fn set(&self) {
        self.is_set.store(true, Ordering::Release);
        self.notify.notify_waiters();
    }

    /// Check if the event is currently set.
    #[must_use]
    pub fn is_set(&self) -> bool {
        self.is_set.load(Ordering::Acquire)
    }

    /// Clear the event, causing future wait
    /// calls to block until the event is set again.
    pub fn clear(&self) {
        self.is_set.store(false, Ordering::Release);
    }
}
