from quantum.domain.types.execution_channel import ExecutionChannel
from quantum.infrastructure.adapters.mt5.adapters.adapter_factory import create_adapter


class Mt5SessionManager:
    def __init__(self):
        self._adapters: dict[ExecutionChannel, object] = {}

    def start(self, channel: ExecutionChannel):
        if channel not in self._adapters:
            self._adapters[channel] = create_adapter(channel)
        return self._adapters[channel]

    def get(self, channel: ExecutionChannel):
        adapter = self._adapters.get(channel)
        if adapter is None:
            raise RuntimeError(f"Session for {channel.name} not started")
        return adapter

    def all_channels(self):
        return list(self._adapters.keys())
