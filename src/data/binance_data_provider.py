from typing import List, Callable
import logging
import asyncio
from core.models.models import Candle
from data.data_provider import DataProvider
import websockets
import json
import aiohttp


class BinanceDataProvider:
    """Proveedor de datos usando Binance WebSocket API"""

    def __init__(self):
        self.ws_url = "wss://stream.binance.com:9443/ws/"
        self.rest_url = "https://api.binance.com/api/v3"
        self.websocket = None
        self.is_connected = False
        self.callbacks = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Conecta con Binance WebSocket"""
        try:
            self.is_connected = True
            self.logger.info("Conectado a Binance WebSocket")
        except Exception as e:
            self.logger.error(f"Error conectando con Binance: {e}")
            raise

    async def subscribe_candles(self, symbol: str, interval: str, callback: Callable):
        """Suscribe a datos de klines en tiempo real"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        self.callbacks[stream_name] = callback

        uri = f"{self.ws_url}{stream_name}"

        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                self.logger.info(f"Suscrito a {symbol} klines {interval}")

                async for message in websocket:
                    data = json.loads(message)
                    await self._process_kline_data(data, callback)

        except Exception as e:
            self.logger.error(f"Error en WebSocket: {e}")
            await asyncio.sleep(5)  # Reconectar después de 5 segundos
            await self.subscribe_candles(symbol, interval, callback)

    async def _process_kline_data(self, data: dict, callback: Callable):
        """Procesa datos de kline recibidos"""
        try:
            kline_data = data["k"]

            candle = Candle(
                timestamp=int(kline_data["t"] / 1000),  # Convertir a segundos
                open=float(kline_data["o"]),
                high=float(kline_data["h"]),
                low=float(kline_data["l"]),
                close=float(kline_data["c"]),
                volume=float(kline_data["v"]),
            )

            # Solo procesar velas cerradas
            if kline_data["x"]:  # is_closed flag
                await callback(candle)

        except Exception as e:
            self.logger.error(f"Error procesando kline data: {e}")

    async def get_historical_data(
        self, symbol: str, interval: str, limit: int = 100
    ) -> List[Candle]:
        """Obtiene datos históricos de klines"""
        url = f"{self.rest_url}/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

            candles = []
            for kline in data:
                candle = Candle(
                    timestamp=int(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                )
                candles.append(candle)

            return candles

        except Exception as e:
            self.logger.error(f"Error obteniendo datos históricos: {e}")
            return []
