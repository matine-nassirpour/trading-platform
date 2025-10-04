from typing import NewType

RunId = NewType("RunId", str)
CorrelationId = NewType("CorrelationId", str)
TraceId = NewType("TraceId", str)
SpanId = NewType("SpanId", str)

ClientOrderId = NewType("ClientOrderId", str)
IntentId = NewType("IntentId", str)
OrderId = NewType("OrderId", int)
DealId = NewType("DealId", int)
PositionId = NewType("PositionId", int)
Symbol = NewType("Symbol", str)
