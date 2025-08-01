from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

class SignalType(Enum):
    CALL = "CALL"
    PUT = "PUT"
    WAIT = "WAIT"

class CandlePattern(Enum):
    DOJI = "DOJI"
    HAMMER = "HAMMER"
    SHOOTING_STAR = "SHOOTING_STAR"
    ENGULFING_BULL = "ENGULFING_BULL"
    ENGULFING_BEAR = "ENGULFING_BEAR"
    REJECTION = "REJECTION"
    PINBAR = "PINBAR"

@dataclass
class Candle:
    """Modelo de datos para una vela"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def upper_shadow(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_shadow(self) -> float:
        return min(self.open, self.close) - self.low
    
    @property
    def total_range(self) -> float:
        return self.high - self.low
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        return self.body_size / self.total_range < 0.1 if self.total_range > 0 else False

@dataclass
class Signal:
    def __init__(self, **entries):
        self.__dict__.update(entries)
    """Modelo para señales de trading"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    confidence: float
    entry_price: float
    expiry_time: int
    reason: str
    support_resistance: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class KeyLevel:
    """Modelo para niveles clave"""
    price: float
    level_type: str  # 'support', 'resistance', 'pivot'
    strength: int  # 1-5
    touch_count: int
    last_touch: datetime
    
    def is_near(self, price: float, tolerance: float = 0.0001) -> bool:
        return abs(self.price - price) <= tolerance