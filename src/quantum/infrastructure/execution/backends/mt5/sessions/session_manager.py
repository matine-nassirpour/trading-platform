from quantum.domain.types.execution_channel import ExecutionChannel
from quantum.infrastructure.execution.backends.mt5.adapters.adapter_factory import (
    create_adapter,
)
from quantum.infrastructure.execution.backends.mt5.adapters.base_adapter import (
    BaseMt5Adapter,
)


class Mt5SessionManager:
    def __init__(self) -> None:
        self._adapters: dict[ExecutionChannel, BaseMt5Adapter] = {}

    def start(self, channel: ExecutionChannel) -> BaseMt5Adapter:
        if channel not in self._adapters:
            self._adapters[channel] = create_adapter(channel)
        return self._adapters[channel]

    def get(self, channel: ExecutionChannel) -> BaseMt5Adapter:
        adapter = self._adapters.get(channel)
        if adapter is None:
            raise RuntimeError(f"Session for {channel.name} not started")
        return adapter

    def all_channels(self) -> list[ExecutionChannel]:
        return list(self._adapters.keys())
