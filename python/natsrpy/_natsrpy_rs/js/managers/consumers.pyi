from typing import overload

from natsrpy._natsrpy_rs.js.consumers import (
    PullConsumer,
    PullConsumerConfig,
    PushConsumer,
    PushConsumerConfig,
)

class ConsumersManager:
    @overload
    async def create(self, config: PullConsumerConfig) -> PullConsumer: ...
    @overload
    async def create(self, config: PushConsumerConfig) -> PushConsumer: ...
