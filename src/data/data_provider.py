from abc import ABC, abstractmethod
from typing import List

from core.models.models import Candle
class DataProvider(ABC):
    """Interfaz abstracta para proveedores de datos"""
    
    @abstractmethod
    async def connect(self):
        pass
    
    @abstractmethod
    async def subscribe_candles(self, symbol: str, timeframe: int):
        pass
    
    @abstractmethod
    async def get_historical_data(self, symbol: str, timeframe: int, count: int) -> List[Candle]:
        pass
