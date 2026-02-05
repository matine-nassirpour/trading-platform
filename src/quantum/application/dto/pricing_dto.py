from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class QuantizedPriceDTO:
    original: Decimal
    quantized: Decimal


@dataclass(frozen=True, slots=True)
class QuantizedVolumeDTO:
    original: Decimal
    quantized: Decimal
