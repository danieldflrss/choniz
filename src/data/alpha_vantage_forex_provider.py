from core.models.models import Candle
from typing import List, Optional
import logging
import asyncio
import aiohttp
import time
from datetime import datetime


class AlphaVantageForexProvider:
    """Proveedor de datos Forex usando Alpha Vantage"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.logger = logging.getLogger(__name__)
        self._last_request = 0
        self._rate_limit = 1  # 1 segundo entre requests
        
    async def get_forex_data(self, from_symbol: str, to_symbol: str) -> Optional[float]:
        """Obtiene cotización actual de forex"""
        # Rate limiting
        current_time = time.time()
        if current_time - self._last_request < self._rate_limit:
            await asyncio.sleep(self._rate_limit - (current_time - self._last_request))
        
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_symbol,
            'to_currency': to_symbol,
            'apikey': self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()
                    
            self._last_request = time.time()
            
            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                return float(rate_data['5. Exchange Rate'])
            else:
                self.logger.warning(f"No se pudo obtener datos para {from_symbol}/{to_symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo datos forex: {e}")
            return None
    
    async def get_intraday_data(self, from_symbol: str, to_symbol: str, interval: str = '1min') -> List[Candle]:
        """Obtiene datos intraday de forex"""
        params = {
            'function': 'FX_INTRADAY',
            'from_symbol': from_symbol,
            'to_symbol': to_symbol,
            'interval': interval,
            'apikey': self.api_key,
            'outputsize': 'compact'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()
            
            time_series_key = f'Time Series FX ({interval})'
            if time_series_key not in data:
                self.logger.warning(f"No hay datos disponibles para {from_symbol}/{to_symbol}")
                return []
            
            candles = []
            time_series = data[time_series_key]
            
            for timestamp_str, ohlc_data in time_series.items():
                timestamp = int(datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp())
                
                candle = Candle(
                    timestamp=timestamp,
                    open=float(ohlc_data['1. open']),
                    high=float(ohlc_data['2. high']),
                    low=float(ohlc_data['3. low']),
                    close=float(ohlc_data['4. close']),
                    volume=0  # Forex no tiene volumen
                )
                candles.append(candle)
            
            # Ordenar por timestamp
            candles.sort(key=lambda x: x.timestamp)
            return candles
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos intraday: {e}")
            return []