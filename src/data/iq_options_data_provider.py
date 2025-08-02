from typing import Callable, Dict, List
from core.models.models import Candle
from data.data_provider import DataProvider
import logging
import queue
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import time
import numpy as np
import asyncio


class IQOptionsDataProvider(DataProvider):
    """Proveedor de datos para IQ Options API"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.ws = None
        self.is_connected = False
        self.candle_queue = queue.Queue()
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Conecta con la API de IQ Options"""
        try:
            # Implementación simplificada - requiere la librería iqoptionapi
            # from iqoptionapi.stable_api import IQ_Option
            self.api = IQ_Option(self.email, self.password)
            check, reason = self.api.connect()

            if check:
                self.is_connected = True
                logging.info("Conectado exitosamente a IQ Option")
                return True
            else:
                logging.error(f"Error de conexión: {reason}")
                return False

        except Exception as e:
            self.logger.error(f"Error conectando a IQ Options: {e}")
            raise

    async def subscribe_candles(self, symbol: str, timeframe: int, callback: Callable):
        """Enhanced version that returns only completed candles, excluding current incomplete candle"""
        if not self.is_connected:
            await self.connect()

        self.api.start_candles_stream(symbol, timeframe, 2)
        self.logger.info(f"Subscribed to {symbol} with timeframe {timeframe}s")

        candle_cache: Dict[int, Candle] = {}
        last_completed_candle_timestamp = None

        try:
            while True:
                candles_data = self.api.get_realtime_candles(symbol, timeframe)

                if candles_data:
                    # Sort candles by timestamp to identify the most recent ones
                    sorted_timestamps = sorted(candles_data.keys())

                    # Process all candles except the most recent one (current incomplete candle)
                    completed_candles = (
                        sorted_timestamps[:-1] if len(sorted_timestamps) > 1 else []
                    )

                    for timestamp in completed_candles:
                        candle_data = candles_data[timestamp]

                        # Check if this is a new completed candle we haven't processed
                        if timestamp not in candle_cache and (
                            last_completed_candle_timestamp is None
                            or timestamp > last_completed_candle_timestamp
                        ):

                            # Create new Candle object
                            new_candle = Candle(
                                timestamp=candle_data["from"],
                                open=float(candle_data["open"]),
                                high=float(candle_data["max"]),
                                low=float(candle_data["min"]),
                                close=float(candle_data["close"]),
                                volume=int(candle_data.get("volume", 1000)),
                            )

                            # Add to cache
                            candle_cache[timestamp] = new_candle
                            last_completed_candle_timestamp = timestamp

                            # Log new completed candle
                            candle_time = datetime.fromtimestamp(timestamp)
                            self.logger.info(
                                f"New candle for {symbol} at {candle_time}"
                            )

                            # Execute callback only for completed candles
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(new_candle)
                                else:
                                    callback(new_candle)
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")

                    # Clean old candles from cache (keep only last 10 completed candles)
                    if len(candle_cache) > 10:
                        oldest_timestamps = sorted(candle_cache.keys())[:-10]
                        for old_timestamp in oldest_timestamps:
                            del candle_cache[old_timestamp]

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            self.logger.info(f"Stopping candle subscription for {symbol}")
        except Exception as e:
            self.logger.error(f"Error in candle subscription: {e}")
            raise

    async def get_historical_data(
        self, symbol: str, timeframe: int, count: int
    ) -> List[Candle]:
        """Obtiene datos históricos"""
        candles = self.api.get_candles(symbol, timeframe, count, time.time())

        # Datos simulados para desarrollo
        historical_data = []

        if not candles:
            return historical_data

        for candle_data in candles:  # type: ignore
            candle = Candle(
                timestamp=candle_data["from"],
                open=float(candle_data["open"]),
                high=float(candle_data["max"]),
                low=float(candle_data["min"]),
                close=float(candle_data["close"]),
                volume=int(
                    candle_data.get("volume", 1000)
                ),  # IQ Option no siempre provee volumen
            )
            historical_data.append(candle)

        return historical_data
