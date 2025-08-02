from typing import Callable, Dict, List, Optional
from core.models.models import Candle, Signal, SignalType
from core.strategy.real_time_scalping_strategy import RealTimeScalpingStrategy
from data.alpha_vantage_forex_provider import AlphaVantageForexProvider
from data.binance_data_provider import BinanceDataProvider
from data.iex_cloud_provider import IEXCloudProvider
from data.iq_options_data_provider import IQOptionsDataProvider
import logging
import time
import asyncio
from datetime import datetime, timedelta
import statistics


class RealTimeMarketSystem:
    """Sistema principal de análisis en tiempo real mejorado"""

    def __init__(
        self, data_source: str = "binance", config: Optional[Dict] = None, **credentials
    ):
        self.data_source = data_source
        self.credentials = credentials
        self.config = config or {}
        self.data_provider = None

        # Inicializar estrategia con configuración
        self.strategy = RealTimeScalpingStrategy(config)

        self.candles_buffer = []

        # Usar configuraciones del sistema si están disponibles
        system_config = self.config.get("system", {})
        self.max_buffer_size = system_config.get("max_buffer_size", 500)
        self.min_history_for_analysis = system_config.get(
            "min_history_for_analysis", 50
        )
        self.historical_data_depth = system_config.get("historical_data_depth", 400)

        self.is_running = False
        self.signal_callbacks = []
        self.logger = self._setup_logger()
        self.current_symbol = ""

        # Configurar filtros desde config
        filters = self.config.get("filters", {})
        self.enable_trend_filter = filters.get("enable_trend_filter", True)
        self.enable_volatility_filter = filters.get("enable_volatility_filter", True)
        self.enable_session_filter = filters.get("enable_session_filter", True)

        # Configurar alertas desde config
        alerts_config = self.config.get("alerts", {})
        self.min_confidence_for_high_priority = alerts_config.get(
            "min_confidence_for_high_priority", 0.80
        )
        self.enable_duplicate_filter = alerts_config.get(
            "enable_duplicate_filter", True
        )
        self.duplicate_timeout = alerts_config.get("duplicate_timeout", 25)

        # Resto de inicialización...
        self.last_candle_timestamp = 0
        self.candle_count = 0
        self.signal_count = 0
        self.signal_history = []

        self.performance_metrics = {
            "signals_generated": 0,
            "last_signal_time": None,
            "avg_signal_interval": 0,
            "candles_processed": 0,
            "data_quality_score": 0.0,
        }

        self._setup_data_provider()

    def _setup_data_provider(self):
        """Configura el proveedor de datos según la fuente"""
        if self.data_source == "iqoptions":
            self.data_provider = IQOptionsDataProvider(
                self.credentials.get("email", ""), self.credentials.get("password", "")
            )
        elif self.data_source == "binance":
            self.data_provider = BinanceDataProvider()
        elif self.data_source == "alphavantage":
            api_key = self.credentials.get("api_key")
            if not api_key:
                raise ValueError("API key requerida para Alpha Vantage")
            self.data_provider = AlphaVantageForexProvider(api_key)
        elif self.data_source == "iex":
            api_token = self.credentials.get("api_token")
            if not api_token:
                raise ValueError("API token requerido para IEX Cloud")
            self.data_provider = IEXCloudProvider(api_token)
        else:
            raise ValueError(f"Fuente de datos no soportada: {self.data_source}")

    def _setup_logger(self):
        """Configura logging avanzado"""
        logger = logging.getLogger(__name__)

        # Usar nivel de logging desde config
        system_config = self.config.get("system", {})
        log_level = system_config.get("log_level", "INFO")
        logger.setLevel(getattr(logging, log_level))

        return logger

    def add_signal_callback(self, callback: Callable):
        """Añade callback para procesar señales"""
        self.signal_callbacks.append(callback)

    async def start_real_time_analysis(self, symbol: str, interval: str = "1m"):
        """Inicia análisis en tiempo real con configuración optimizada"""
        try:
            self.logger.info(f"🚀 Iniciando análisis optimizado para {symbol}")
            self.current_symbol = symbol

            # Pre-cargar datos históricos con más profundidad
            await self._preload_historical_data(symbol, interval)

            # Iniciar análisis según fuente de datos
            if self.data_source == "iqoptions":
                await self._start_iqoptions_analysis(symbol, interval)
            elif self.data_source == "binance":
                await self._start_binance_analysis(symbol, interval)
            elif self.data_source == "alphavantage":
                await self._start_forex_analysis(symbol)
            elif self.data_source == "iex":
                await self._start_stock_analysis(symbol)

            self.is_running = True

            # Iniciar tareas de mantenimiento
            asyncio.create_task(self._performance_monitor())
            asyncio.create_task(self._data_quality_monitor())

        except Exception as e:
            self.logger.error(f"❌ Error iniciando análisis: {e}")
            raise

    async def _preload_historical_data(self, symbol: str, interval: str):
        """Pre-carga datos históricos para mejor precisión"""
        try:
            if self.data_source == "iqoptions":
                await self.data_provider.connect()
                historical_data = await self.data_provider.get_historical_data(
                    symbol, 60, self.historical_data_depth
                )
                if historical_data:
                    self.candles_buffer = historical_data[-self.max_buffer_size :]
                    self.logger.info(
                        f"📊 Cargadas {len(self.candles_buffer)} velas históricas"
                    )

            elif self.data_source == "binance":
                await self.data_provider.connect()
                historical_data = await self.data_provider.get_historical_data(
                    symbol, interval, 200
                )
                if historical_data:
                    self.candles_buffer = historical_data
                    self.logger.info(
                        f"📊 Cargadas {len(self.candles_buffer)} velas de Binance"
                    )

            # Validar calidad de datos históricos
            if self.candles_buffer:
                self._validate_historical_data()

        except Exception as e:
            self.logger.error(f"Error pre-cargando datos: {e}")

    def _validate_historical_data(self):
        """Valida la calidad de los datos históricos"""
        if not self.candles_buffer:
            return

        # Verificar continuidad temporal
        gaps = 0
        for i in range(1, len(self.candles_buffer)):
            time_diff = (
                self.candles_buffer[i].timestamp - self.candles_buffer[i - 1].timestamp
            )
            if time_diff > 120:  # Gap mayor a 2 minutos
                gaps += 1

        # Verificar precios válidos
        invalid_prices = sum(
            1
            for c in self.candles_buffer
            if c.open <= 0 or c.high <= 0 or c.low <= 0 or c.close <= 0
        )

        data_quality = max(0, 1 - (gaps + invalid_prices) / len(self.candles_buffer))
        self.performance_metrics["data_quality_score"] = data_quality

        self.logger.info(
            f"📈 Calidad de datos: {data_quality:.2%} | Gaps: {gaps} | Precios inválidos: {invalid_prices}"
        )

    async def _start_iqoptions_analysis(self, symbol: str, interval: str):
        """Análisis optimizado para IQ Options"""
        try:
            # Convertir interval a segundos
            interval_seconds = 60 if interval == "1m" else int(interval)

            # Suscribirse a datos en tiempo real con callback optimizado
            await self.data_provider.subscribe_candles(
                symbol, interval_seconds, self._on_new_candle_enhanced
            )

        except Exception as e:
            self.logger.error(f"Error en análisis IQ Options: {e}")
            # Implementar reconexión automática
            await asyncio.sleep(10)
            await self._start_iqoptions_analysis(symbol, interval)

    async def _start_binance_analysis(self, symbol: str, interval: str):
        """Análisis optimizado para Binance"""
        try:
            await self.data_provider.subscribe_candles(
                symbol, interval, self._on_new_candle_enhanced
            )
        except Exception as e:
            self.logger.error(f"Error en análisis Binance: {e}")
            await asyncio.sleep(10)
            await self._start_binance_analysis(symbol, interval)

    async def _start_forex_analysis(self, symbol: str):
        """Análisis optimizado para Forex"""
        from_symbol, to_symbol = symbol.split("/")

        # Obtener datos históricos iniciales
        historical_data = await self.data_provider.get_intraday_data(
            from_symbol, to_symbol, "1min"
        )
        if historical_data:
            self.candles_buffer.extend(historical_data[-100:])

        # Polling optimizado
        while self.is_running:
            try:
                current_rate = await self.data_provider.get_forex_data(
                    from_symbol, to_symbol
                )

                if current_rate:
                    timestamp = int(time.time())
                    last_candle = (
                        self.candles_buffer[-1] if self.candles_buffer else None
                    )

                    if last_candle and timestamp - last_candle.timestamp >= 60:
                        new_candle = Candle(
                            timestamp=timestamp,
                            open=last_candle.close,
                            high=max(last_candle.close, current_rate),
                            low=min(last_candle.close, current_rate),
                            close=current_rate,
                            volume=0,
                        )
                        await self._on_new_candle_enhanced(new_candle)

                await asyncio.sleep(30)  # Polling cada 30 segundos

            except Exception as e:
                self.logger.error(f"Error en forex polling: {e}")
                await asyncio.sleep(60)

    async def _start_stock_analysis(self, symbol: str):
        """Análisis optimizado para acciones"""
        # Similar al forex pero con datos de acciones
        historical_data = await self.data_provider.get_chart_data(symbol, "1d")
        if historical_data:
            self.candles_buffer.extend(historical_data[-100:])

        while self.is_running:
            try:
                quote = await self.data_provider.get_quote(symbol)

                if quote and "latestPrice" in quote:
                    timestamp = int(time.time())
                    current_price = float(quote["latestPrice"])
                    last_candle = (
                        self.candles_buffer[-1] if self.candles_buffer else None
                    )

                    if last_candle and timestamp - last_candle.timestamp >= 60:
                        new_candle = Candle(
                            timestamp=timestamp,
                            open=last_candle.close,
                            high=max(last_candle.close, current_price),
                            low=min(last_candle.close, current_price),
                            close=current_price,
                            volume=quote.get("latestVolume", 0),
                        )
                        await self._on_new_candle_enhanced(new_candle)

                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Error en stock polling: {e}")
                await asyncio.sleep(30)

    async def _on_new_candle_enhanced(self, candle: Candle):
        """Procesamiento mejorado de nuevas velas"""
        try:
            # Evitar velas duplicadas
            if (
                self.candles_buffer
                and self.candles_buffer[-1].timestamp >= candle.timestamp
            ):
                return

            # Validar datos de la vela
            if not self._validate_candle(candle):
                self.logger.warning("⚠️ Vela inválida descartada")
                return

            # Añadir a buffer
            self.candles_buffer.append(candle)

            # Mantener tamaño del buffer
            if len(self.candles_buffer) > self.max_buffer_size:
                self.candles_buffer = self.candles_buffer[-self.max_buffer_size :]

            # Actualizar métricas
            self.candle_count += 1
            self.performance_metrics["candles_processed"] += 1
            self.last_candle_timestamp = candle.timestamp

            # Log optimizado (cada 10 velas)
            if self.candle_count % 10 == 0:
                self.logger.info(
                    f"📊 Vela #{self.candle_count}: {candle.close:.5f} | "
                    f"Buffer: {len(self.candles_buffer)} | "
                    f"Señales: {self.signal_count}"
                )

            # Análisis de señales solo si tenemos suficiente historia
            if len(self.candles_buffer) >= 50:
                # Aplicar filtros pre-análisis
                if self._should_analyze_candle(candle):
                    signal = self.strategy.analyze_real_time(
                        self.candles_buffer, self.current_symbol
                    )

                    if signal:
                        # Validar señal con filtros adicionales
                        if await self._validate_signal(signal):
                            await self._process_signal_enhanced(signal)

        except Exception as e:
            self.logger.error(f"❌ Error procesando vela: {e}")

    def _validate_candle(self, candle: Candle) -> bool:
        """Valida datos de una vela"""
        # Verificar precios válidos
        if any(
            price <= 0 for price in [candle.open, candle.high, candle.low, candle.close]
        ):
            return False

        # Verificar lógica OHLC
        if not (
            candle.low <= candle.open <= candle.high
            and candle.low <= candle.close <= candle.high
        ):
            return False

        # Verificar que high es el máximo y low es el mínimo
        if candle.high < max(candle.open, candle.close):
            return False
        if candle.low > min(candle.open, candle.close):
            return False

        return True

    def _should_analyze_candle(self, candle: Candle) -> bool:
        """Determina si se debe analizar una vela para señales"""

        # Filtro de sesión de trading
        if self.enable_session_filter:
            current_hour = datetime.fromtimestamp(candle.timestamp).hour
            # Evitar horas de baja liquidez y noticias importantes
            if current_hour in []:  # [0, 1, 2, 3, 4, 5, 22, 23]:
                return False

        # Filtro de volatilidad mínima
        if self.enable_volatility_filter and len(self.candles_buffer) >= 10:
            recent_ranges = [c.total_range for c in self.candles_buffer[-10:]]
            avg_range = sum(recent_ranges) / len(recent_ranges)

            if candle.total_range < avg_range * 0.3:  # Muy baja volatilidad
                return False

        # Filtro de tendencia (evitar mercados laterales extremos)
        if self.enable_trend_filter and len(self.candles_buffer) >= 20:
            closes = [c.close for c in self.candles_buffer[-20:]]
            price_range = max(closes) - min(closes)
            current_price = candle.close

            # Si el precio está muy concentrado, evitar señales
            if price_range < current_price * 0.001:  # Menos del 0.1% de rango
                return False

        return True

    async def _validate_signal(self, signal: Signal) -> bool:
        """Validación avanzada de señales"""

        # Evitar señales muy frecuentes del mismo tipo
        if len(self.signal_history) >= 3:
            recent_signals = self.signal_history[-3:]
            same_type_count = sum(
                1 for s in recent_signals if s.signal_type == signal.signal_type
            )

            if same_type_count >= 2:  # Máximo 2 señales del mismo tipo consecutivas
                return False

        # Validar que la confianza sea suficiente para el contexto actual
        if len(self.candles_buffer) >= 10:
            recent_volatility = statistics.stdev(
                [c.close for c in self.candles_buffer[-10:]]
            )
            current_price = self.candles_buffer[-1].close
            volatility_ratio = recent_volatility / current_price

            # Ajustar umbral de confianza según volatilidad
            min_confidence = 0.6 if volatility_ratio > 0.002 else 0.7

            if signal.confidence < min_confidence:
                return False

        # Filtro de distancia a niveles importantes
        if signal.support_resistance:
            distance = (
                abs(signal.entry_price - signal.support_resistance) / signal.entry_price
            )
            if distance > 0.005:  # Más del 0.5% de distancia
                return False

        return True

    async def _process_signal_enhanced(self, signal: Signal):
        """Procesamiento mejorado de señales"""

        # Actualizar métricas
        self.signal_count += 1
        self.performance_metrics["signals_generated"] += 1
        self.performance_metrics["last_signal_time"] = signal.timestamp

        # Calcular intervalo promedio entre señales
        if len(self.signal_history) > 0:
            time_diff = signal.timestamp - self.signal_history[-1].timestamp
            intervals = [time_diff.total_seconds()]

            if len(self.signal_history) >= 10:
                for i in range(1, min(11, len(self.signal_history))):
                    prev_diff = (
                        self.signal_history[-i].timestamp
                        - self.signal_history[-i - 1].timestamp
                    ).total_seconds()
                    intervals.append(prev_diff)

            self.performance_metrics["avg_signal_interval"] = statistics.mean(intervals)

        # Añadir a historial
        self.signal_history.append(signal)

        # Mantener historial limitado
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]

        # Enriquecer señal con contexto adicional
        enriched_signal = self._enrich_signal(signal)

        # Log detallado
        self.logger.info(
            f"\n🎯 SEÑAL #{self.signal_count}: {signal.signal_type.value}\n"
            f"💰 Precio: {signal.entry_price:.5f}\n"
            f"🎲 Confianza: {signal.confidence:.1%}\n"
            f"🕐 Fecha: {signal.timestamp.strftime('%H:%M:%S')}\n"
            f"⏱️ Expiración: {signal.expiry_time}s\n"
            f"📊 Razón: {signal.reason}\n"
            f"🎯 S/R: {signal.support_resistance}\n"
            f"📈 Contexto: {self._get_market_context()}"
        )

        # Ejecutar callbacks
        for callback in self.signal_callbacks:
            try:
                await callback(enriched_signal)
            except Exception as e:
                self.logger.error(f"❌ Error en callback: {e}")

    def _enrich_signal(self, signal: Signal) -> Signal:
        """Enriquece la señal con información adicional del contexto"""

        # Calcular fuerza de la tendencia
        if len(self.candles_buffer) >= 20:
            closes = [c.close for c in self.candles_buffer[-20:]]
            trend_strength = (closes[-1] - closes[0]) / closes[0]

            # Añadir información de tendencia a la razón
            if abs(trend_strength) > 0.01:  # Tendencia significativa
                trend_info = f"Tendencia fuerte ({'alcista' if trend_strength > 0 else 'bajista'})"
                signal.reason += f"; {trend_info}"

        # Calcular contexto de volatilidad
        if len(self.candles_buffer) >= 10:
            recent_ranges = [c.total_range for c in self.candles_buffer[-10:]]
            avg_range = sum(recent_ranges) / len(recent_ranges)
            current_volatility = self.candles_buffer[-1].total_range / avg_range

            if current_volatility > 1.5:
                signal.reason += "; Alta volatilidad"
            elif current_volatility < 0.7:
                signal.reason += "; Baja volatilidad"

        return signal

    def _get_market_context(self) -> str:
        """Obtiene contexto actual del mercado"""
        if not self.candles_buffer:
            return "Sin datos"

        current_candle = self.candles_buffer[-1]
        current_time = datetime.fromtimestamp(current_candle.timestamp)

        # Determinar sesión
        hour = current_time.hour
        if 8 <= hour < 17:
            session = "Europea/Americana"
        elif 0 <= hour < 8:
            session = "Asiática"
        else:
            session = "Solapamiento"

        # Calcular momentum reciente
        if len(self.candles_buffer) >= 5:
            momentum = self.candles_buffer[-1].close - self.candles_buffer[-5].close
            momentum_str = f"{'↗️' if momentum > 0 else '↘️'} {abs(momentum):.5f}"
        else:
            momentum_str = "N/A"

        return f"{session} | Mom: {momentum_str}"

    async def _performance_monitor(self):
        """Monitor de rendimiento en segundo plano"""
        while self.is_running:
            try:
                # Calcular estadísticas cada 5 minutos
                await asyncio.sleep(300)

                if self.signal_count > 0:
                    win_rate = self._calculate_estimated_win_rate()
                    signal_frequency = self.signal_count / max(
                        1, self.candle_count / 60
                    )  # señales por hora

                    self.logger.info(
                        f"📊 RENDIMIENTO | Señales: {self.signal_count} | "
                        f"Frecuencia: {signal_frequency:.1f}/h | "
                        f"Win Rate Est.: {win_rate:.1%} | "
                        f"Calidad datos: {self.performance_metrics['data_quality_score']:.1%}"
                    )

            except Exception as e:
                self.logger.error(f"Error en monitor de rendimiento: {e}")

    async def _data_quality_monitor(self):
        """Monitor de calidad de datos"""
        while self.is_running:
            try:
                await asyncio.sleep(600)  # Cada 10 minutos

                if len(self.candles_buffer) >= 10:
                    # Verificar gaps en datos
                    gaps = 0
                    for i in range(1, min(50, len(self.candles_buffer))):
                        time_diff = (
                            self.candles_buffer[-i].timestamp
                            - self.candles_buffer[-i - 1].timestamp
                        )
                        if time_diff > 120:  # Gap mayor a 2 minutos
                            gaps += 1

                    if gaps > 5:
                        self.logger.warning(
                            f"⚠️ Calidad de datos degradada: {gaps} gaps detectados"
                        )

                        # Intentar reconexión si hay muchos gaps
                        if gaps > 15:
                            self.logger.info(
                                "🔄 Intentando reconexión por baja calidad de datos..."
                            )
                            await self._reconnect_data_source()

            except Exception as e:
                self.logger.error(f"Error en monitor de calidad: {e}")

    async def _reconnect_data_source(self):
        """Reconecta la fuente de datos"""
        try:
            self.logger.info("🔄 Reconectando fuente de datos...")

            if hasattr(self.data_provider, "connect"):
                await self.data_provider.connect()

            # Reiniciar suscripción
            if self.data_source == "iqoptions":
                interval_seconds = 60
                await self.data_provider.subscribe_candles(
                    self.current_symbol, interval_seconds, self._on_new_candle_enhanced
                )

            self.logger.info("✅ Reconexión exitosa")

        except Exception as e:
            self.logger.error(f"❌ Error en reconexión: {e}")

    def _calculate_estimated_win_rate(self) -> float:
        """Calcula win rate estimado basado en señales históricas"""
        if len(self.signal_history) < 10:
            return 0.5  # Valor por defecto

        # Análisis simplificado basado en confianza de señales
        high_confidence_signals = [
            s for s in self.signal_history[-50:] if s.confidence > 0.8
        ]
        medium_confidence_signals = [
            s for s in self.signal_history[-50:] if 0.6 <= s.confidence <= 0.8
        ]

        # Estimación basada en confianza (aproximada)
        estimated_win_rate = (
            len(high_confidence_signals) * 0.75 + len(medium_confidence_signals) * 0.6
        ) / len(self.signal_history[-50:])

        return min(max(estimated_win_rate, 0.3), 0.9)  # Limitar entre 30% y 90%

    def stop(self):
        """Detiene el sistema con limpieza completa"""
        self.is_running = False

        # Estadísticas finales
        if self.signal_count > 0:
            total_time = time.time() - (
                self.last_candle_timestamp - self.candle_count * 60
            )
            avg_signals_per_hour = self.signal_count / max(1, total_time / 3600)

            self.logger.info(
                f"🏁 RESUMEN FINAL:\n"
                f"📊 Velas procesadas: {self.candle_count}\n"
                f"🎯 Señales generadas: {self.signal_count}\n"
                f"⚡ Promedio señales/hora: {avg_signals_per_hour:.1f}\n"
                f"🎲 Confianza promedio: {statistics.mean([s.confidence for s in self.signal_history[-20:]]) if self.signal_history else 0:.1%}\n"
                f"📈 Calidad de datos: {self.performance_metrics['data_quality_score']:.1%}"
            )

        self.logger.info("🛑 Sistema detenido correctamente")

    def get_real_time_status(self) -> Dict:
        """Estado en tiempo real del sistema mejorado"""
        latest_candle = self.candles_buffer[-1] if self.candles_buffer else None

        status = {
            "is_running": self.is_running,
            "data_source": self.data_source,
            "symbol": self.current_symbol,
            "candles_count": len(self.candles_buffer),
            "signals_generated": self.signal_count,
            "latest_candle": (
                {
                    "timestamp": (
                        datetime.fromtimestamp(latest_candle.timestamp).isoformat()
                        if latest_candle
                        else None
                    ),
                    "price": latest_candle.close if latest_candle else None,
                    "volume": latest_candle.volume if latest_candle else None,
                    "range": latest_candle.total_range if latest_candle else None,
                }
                if latest_candle
                else None
            ),
            "performance_metrics": self.performance_metrics,
            "filters_enabled": {
                "trend_filter": self.enable_trend_filter,
                "volatility_filter": self.enable_volatility_filter,
                "session_filter": self.enable_session_filter,
            },
            "last_update": datetime.now().isoformat(),
            "estimated_win_rate": (
                self._calculate_estimated_win_rate() if self.signal_count > 0 else None
            ),
            "market_context": self._get_market_context(),
        }

        return status

    def get_signal_statistics(self) -> Dict:
        """Estadísticas detalladas de señales"""
        if not self.signal_history:
            return {}

        recent_signals = self.signal_history[-50:]  # Últimas 50 señales

        call_signals = [s for s in recent_signals if s.signal_type == SignalType.CALL]
        put_signals = [s for s in recent_signals if s.signal_type == SignalType.PUT]

        return {
            "total_signals": len(recent_signals),
            "call_signals": len(call_signals),
            "put_signals": len(put_signals),
            "call_percentage": (
                len(call_signals) / len(recent_signals) * 100 if recent_signals else 0
            ),
            "avg_confidence": statistics.mean([s.confidence for s in recent_signals]),
            "max_confidence": max(s.confidence for s in recent_signals),
            "min_confidence": min(s.confidence for s in recent_signals),
            "avg_expiry_time": statistics.mean([s.expiry_time for s in recent_signals]),
            "signals_last_hour": len(
                [
                    s
                    for s in recent_signals
                    if (datetime.now() - s.timestamp).total_seconds() < 3600
                ]
            ),
            "most_common_reasons": self._get_most_common_reasons(recent_signals),
        }

    def _get_most_common_reasons(self, signals: List[Signal]) -> Dict[str, int]:
        """Obtiene las razones más comunes de las señales"""
        reason_count = {}

        for signal in signals:
            reasons = signal.reason.split(";")
            for reason in reasons:
                reason = reason.strip()
                if reason:
                    reason_count[reason] = reason_count.get(reason, 0) + 1

        # Retornar top 5
        sorted_reasons = sorted(reason_count.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_reasons[:5])

    def configure_filters(
        self,
        trend_filter: bool = None,
        volatility_filter: bool = None,
        session_filter: bool = None,
    ):
        """Configura filtros del sistema"""
        if trend_filter is not None:
            self.enable_trend_filter = trend_filter
        if volatility_filter is not None:
            self.enable_volatility_filter = volatility_filter
        if session_filter is not None:
            self.enable_session_filter = session_filter

        self.logger.info(
            f"🔧 Filtros configurados - Tendencia: {self.enable_trend_filter} | "
            f"Volatilidad: {self.enable_volatility_filter} | "
            f"Sesión: {self.enable_session_filter}"
        )
