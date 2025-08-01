from typing import Callable, Dict
from core.models.models import Candle, Signal
from core.strategy.real_time_scalping_strategy import RealTimeScalpingStrategy
from data.alpha_vantage_forex_provider import AlphaVantageForexProvider
from data.binance_data_provider import BinanceDataProvider
from data.iex_cloud_provider import IEXCloudProvider
import logging
import time
import asyncio
from datetime import datetime

from data.iq_options_data_provider import IQOptionsDataProvider


class RealTimeMarketSystem:
    """Sistema principal de análisis en tiempo real"""
    
    def __init__(self, data_source: str = "binance", **credentials):
        self.data_source = data_source
        self.credentials = credentials
        self.data_provider = None
        self.strategy = RealTimeScalpingStrategy()
        self.candles_buffer = []
        self.max_buffer_size = 200
        self.is_running = False
        self.signal_callbacks = []
        self.logger = self._setup_logger()
        self.current_symbol = ""
        
        # Configurar proveedor de datos
        self._setup_data_provider()
    
    def _setup_data_provider(self):
        """Configura el proveedor de datos según la fuente"""
        if self.data_source == "iqoptions":
            self.data_provider = IQOptionsDataProvider(self.credentials.get('email', ''), self.credentials.get('password', ''))
        elif self.data_source == "binance":
            self.data_provider = BinanceDataProvider()
        elif self.data_source == "alphavantage":
            api_key = self.credentials.get('api_key')
            if not api_key:
                raise ValueError("API key requerida para Alpha Vantage")
            self.data_provider = AlphaVantageForexProvider(api_key)
        elif self.data_source == "iex":
            api_token = self.credentials.get('api_token')
            if not api_token:
                raise ValueError("API token requerido para IEX Cloud")
            self.data_provider = IEXCloudProvider(api_token)
        else:
            raise ValueError(f"Fuente de datos no soportada: {self.data_source}")
    
    def _setup_logger(self):
        """Configura logging avanzado"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # if not logger.handlers:
        #     handler = logging.StreamHandler()
        #     formatter = logging.Formatter(
        #         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        #     )
        #     handler.setFormatter(formatter)
        #     logger.addHandler(handler)
        
        return logger
    
    def add_signal_callback(self, callback: Callable):
        """Añade callback para procesar señales"""
        self.signal_callbacks.append(callback)
    
    async def start_real_time_analysis(self, symbol: str, interval: str = "1m"):
        """Inicia análisis en tiempo real"""
        try:
            self.logger.info(f"Iniciando análisis en tiempo real para {symbol}")
            self.current_symbol = symbol
            
            # Obtener datos históricos iniciales
            if self.data_source == "iqoptions":
                await self.data_provider.connect()
                historical_data = await self.data_provider.get_historical_data(
                    symbol, interval, 200
                )
                self.candles_buffer = historical_data
                
                # Suscribirse a datos en tiempo real
                await self.data_provider.subscribe_candles(
                    symbol, interval, self._on_new_candle
                )
            elif self.data_source == "binance":
                await self.data_provider.connect()
                historical_data = await self.data_provider.get_historical_data(
                    symbol, interval, 50
                )
                self.candles_buffer = historical_data
                
                # Suscribirse a datos en tiempo real
                await self.data_provider.subscribe_candles(
                    symbol, interval, self._on_new_candle
                )
                
            elif self.data_source == "alphavantage":
                # Para forex, usar polling cada minuto
                await self._start_forex_polling(symbol)
                
            elif self.data_source == "iex":
                # Para acciones, usar polling
                await self._start_stock_polling(symbol)
            
            self.is_running = True
            
        except Exception as e:
            self.logger.error(f"Error iniciando análisis: {e}")
            raise
    
    async def _on_new_candle(self, candle: Candle):
        """Procesa nueva vela recibida"""
        try:
            if self.candles_buffer[-1].timestamp == candle.timestamp:
                return
            # Añadir a buffer
            self.candles_buffer.append(candle)
            
            # Mantener tamaño del buffer
            if len(self.candles_buffer) > self.max_buffer_size:
                self.candles_buffer = self.candles_buffer[-self.max_buffer_size:]
            
            self.logger.info(
                f"Nueva vela: O:{candle.open:.5f} H:{candle.high:.5f} "
                f"L:{candle.low:.5f} C:{candle.close:.5f}"
                f"Time: {candle.timestamp}"
            )
            
            # Analizar
            signal = self.strategy.analyze_real_time(self.candles_buffer,  self.current_symbol)
            
            if signal:
                await self._process_signal(signal)
                
        except Exception as e:
            self.logger.error(f"Error procesando nueva vela: {e}")
    
    async def _start_forex_polling(self, symbol: str):
        """Inicia polling para datos forex"""
        from_symbol, to_symbol = symbol.split('/')
        
        # Obtener datos históricos iniciales
        historical_data = await self.data_provider.get_intraday_data(
            from_symbol, to_symbol, '1min'
        )
        self.candles_buffer = historical_data[-50:] if historical_data else []
        
        # Polling cada 60 segundos
        while self.is_running:
            try:
                current_rate = await self.data_provider.get_forex_data(
                    from_symbol, to_symbol
                )
                
                if current_rate:
                    # Crear vela simulada basada en el precio actual
                    timestamp = int(time.time())
                    last_candle = self.candles_buffer[-1] if self.candles_buffer else None
                    
                    if last_candle and timestamp - last_candle.timestamp >= 60:
                        # Nueva vela cada minuto
                        new_candle = Candle(
                            timestamp=timestamp,
                            open=last_candle.close,
                            high=max(last_candle.close, current_rate),
                            low=min(last_candle.close, current_rate),
                            close=current_rate,
                            volume=0
                        )
                        await self._on_new_candle(new_candle)
                
                await asyncio.sleep(60)  # Esperar 1 minuto
                
            except Exception as e:
                self.logger.error(f"Error en forex polling: {e}")
                await asyncio.sleep(60)
    
    async def _start_stock_polling(self, symbol: str):
        """Inicia polling para datos de acciones"""
        # Obtener datos históricos iniciales
        historical_data = await self.data_provider.get_chart_data(symbol, '1d')
        self.candles_buffer = historical_data[-50:] if historical_data else []
        
        # Polling cada 30 segundos durante horas de mercado
        while self.is_running:
            try:
                quote = await self.data_provider.get_quote(symbol)
                
                if quote and 'latestPrice' in quote:
                    timestamp = int(time.time())
                    current_price = float(quote['latestPrice'])
                    last_candle = self.candles_buffer[-1] if self.candles_buffer else None
                    
                    if last_candle and timestamp - last_candle.timestamp >= 60:
                        # Nueva vela cada minuto
                        new_candle = Candle(
                            timestamp=timestamp,
                            open=last_candle.close,
                            high=max(last_candle.close, current_price),
                            low=min(last_candle.close, current_price),
                            close=current_price,
                            volume=quote.get('latestVolume', 0)
                        )
                        await self._on_new_candle(new_candle)
                
                await asyncio.sleep(30)  # Polling cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en stock polling: {e}")
                await asyncio.sleep(30)
    
    async def _process_signal(self, signal: Signal):
        """Procesa señal generada"""
        self.logger.info(
            f"\n🚨 SEÑAL EN TIEMPO REAL: {signal.signal_type.value} \n"
            f"Símbolo: {signal.symbol} \n"
            f"Confianza: {signal.confidence:.1%} \n"
            f"Precio: {signal.entry_price:.5f} \n"
            f"Razón: {signal.reason}"
        )
        
        # Ejecutar callbacks
        for callback in self.signal_callbacks:
            try:
                await callback(signal)
            except Exception as e:
                self.logger.error(f"Error en callback de señal: {e}")
    
    def stop(self):
        """Detiene el sistema"""
        self.is_running = False
        self.logger.info("Sistema detenido")
    
    def get_real_time_status(self) -> Dict:
        """Estado en tiempo real del sistema"""
        latest_candle = self.candles_buffer[-1] if self.candles_buffer else None
        
        return {
            'is_running': self.is_running,
            'data_source': self.data_source,
            'candles_count': len(self.candles_buffer),
            'latest_candle': {
                'timestamp': datetime.fromtimestamp(latest_candle.timestamp).isoformat() if latest_candle else None,
                'price': latest_candle.close if latest_candle else None,
                'volume': latest_candle.volume if latest_candle else None
            } if latest_candle else None,
            'buffer_size': len(self.candles_buffer),
            'last_update': datetime.now().isoformat()
        }