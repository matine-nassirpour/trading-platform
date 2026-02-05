from quantum.application.services.trading_intent_service import TradingIntentService


class EvaluateTradingIntentUseCase:

    def __init__(self, service: TradingIntentService):
        self._service = service

    def execute(self, intent_id, result):
        if result.authorized:
            self._service.authorize(intent_id, result)
        else:
            self._service.reject(intent_id, result)
