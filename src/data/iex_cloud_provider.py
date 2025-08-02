from typing import List, Optional
from core.models.models import Candle
import time
import logging
import aiohttp
from datetime import datetime


class IEXCloudProvider:
    """Proveedor de datos usando IEX Cloud API"""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://cloud.iexapis.com/stable"
        self.logger = logging.getLogger(__name__)

    async def get_quote(self, symbol: str) -> Optional[dict]:
        """Obtiene cotización en tiempo real"""
        url = f"{self.base_url}/stock/{symbol}/quote"
        params = {"token": self.api_token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    return data
        except Exception as e:
            self.logger.error(f"Error obteniendo cotización: {e}")
            return None

    async def get_chart_data(
        self, symbol: str, range_period: str = "1d"
    ) -> List[Candle]:
        """Obtiene datos de gráfico"""
        url = f"{self.base_url}/stock/{symbol}/chart/{range_period}"
        params = {"token": self.api_token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

            candles = []
            for bar in data:
                if all(k in bar for k in ["open", "high", "low", "close"]):
                    # Combinar fecha y hora si están disponibles
                    if "date" in bar and "minute" in bar:
                        dt_str = f"{bar['date']} {bar['minute']}"
                        timestamp = int(
                            datetime.strptime(dt_str, "%Y-%m-%d %H:%M").timestamp()
                        )
                    elif "date" in bar:
                        timestamp = int(
                            datetime.strptime(bar["date"], "%Y-%m-%d").timestamp()
                        )
                    else:
                        timestamp = int(time.time())

                    candle = Candle(
                        timestamp=timestamp,
                        open=float(bar["open"]) if bar["open"] else 0.0,
                        high=float(bar["high"]) if bar["high"] else 0.0,
                        low=float(bar["low"]) if bar["low"] else 0.0,
                        close=float(bar["close"]) if bar["close"] else 0.0,
                        volume=float(bar.get("volume", 0)),
                    )
                    candles.append(candle)

            return candles

        except Exception as e:
            self.logger.error(f"Error obteniendo datos de gráfico: {e}")
