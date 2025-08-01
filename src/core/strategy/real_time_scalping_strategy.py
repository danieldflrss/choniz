from typing import List, Optional, Tuple
from core.analysis.technical_analysis import TechnicalAnalysis
from core.models.models import Candle, CandlePattern, KeyLevel, Signal, SignalType
from datetime import datetime
import logging
import time


class RealTimeScalpingStrategy:
    """Estrategia avanzada de scalping con datos en tiempo real"""
    
    def __init__(self):
        self.technical_analysis = TechnicalAnalysis()
        self.logger = logging.getLogger(__name__)
        self.last_signal_time = 0
        self.min_signal_interval = 30  # Mínimo 30 segundos entre señales
        self.symbol = ""
        
    def analyze_real_time(self, candles: List[Candle], symbol: str) -> Optional[Signal]:
        """Análisis en tiempo real optimizado"""
        if len(candles) < 25:
            return None
        
        self.symbol = symbol
        
        # Evitar señales muy frecuentes
        current_time = time.time()
        if current_time - self.last_signal_time < self.min_signal_interval:
            return None
        
        current_candle = candles[-1]
        closes = [c.close for c in candles]
        
        # Indicadores técnicos
        ema20 = self.technical_analysis.calculate_ema(closes, 20)
        rsi = self.technical_analysis.calculate_rsi(closes, 9)
        
        if not ema20 or not rsi:
            return None
        
        current_ema = ema20[-1]
        current_rsi = rsi[-1]
        
        # Niveles dinámicos
        key_levels = self.technical_analysis.find_dynamic_support_resistance(candles)
        
        # Patrones de velas
        patterns = self.technical_analysis.identify_advanced_patterns(candles[-5:])
        
        # Análisis multi-factor
        signal = self._multi_factor_analysis(
            current_candle, current_ema, current_rsi, key_levels, patterns, candles
        )
        
        if signal:
            self.last_signal_time = current_time
        
        return signal
    
    def _multi_factor_analysis(self, candle: Candle, ema20: float, rsi: float, 
                              key_levels: List[KeyLevel], patterns: List[Tuple[CandlePattern, int]], 
                              candles: List[Candle]) -> Optional[Signal]:
        """Análisis multifactor para generar señales"""
        
        confidence = 0.0
        signal_type = SignalType.WAIT
        reasons = []
        
        # Factor 1: Tendencia (EMA)
        if candle.close > ema20:
            confidence += 0.2
            trend_bullish = True
        else:
            confidence += 0.2
            trend_bullish = False
        
        # Factor 2: RSI
        if rsi < 30:  # Sobreventa
            confidence += 0.2
            reasons.append("RSI sobreventa")
            if trend_bullish:
                signal_type = SignalType.CALL
        elif rsi > 70:  # Sobrecompra
            confidence += 0.2
            reasons.append("RSI sobrecompra")
            if not trend_bullish:
                signal_type = SignalType.PUT
        
        # Factor 3: Niveles clave
        near_support = False
        near_resistance = False
        
        for level in key_levels:
            if level.is_near(candle.close, tolerance=0.0002):
                if level.level_type == 'support' and candle.close <= level.price:
                    confidence += 0.3 * (level.strength / 5)
                    reasons.append(f"Cerca de soporte {level.price:.5f}")
                    near_support = True
                    if trend_bullish:
                        signal_type = SignalType.CALL
                        
                elif level.level_type == 'resistance' and candle.close >= level.price:
                    confidence += 0.3 * (level.strength / 5)
                    reasons.append(f"Cerca de resistencia {level.price:.5f}")
                    near_resistance = True
                    if not trend_bullish:
                        signal_type = SignalType.PUT
        
        # Factor 4: Patrones de velas
        for pattern, index in patterns:
            if index >= len(candles) - 2:  # Patrones recientes
                if pattern in [CandlePattern.HAMMER, CandlePattern.ENGULFING_BULL]:
                    confidence += 0.25
                    reasons.append(f"Patrón alcista: {pattern.value}")
                    if trend_bullish and near_support:
                        signal_type = SignalType.CALL
                        
                elif pattern in [CandlePattern.SHOOTING_STAR, CandlePattern.ENGULFING_BEAR]:
                    confidence += 0.25
                    reasons.append(f"Patrón bajista: {pattern.value}")
                    if not trend_bullish and near_resistance:
                        signal_type = SignalType.PUT
                
                elif pattern == CandlePattern.PINBAR:
                    confidence += 0.2
                    reasons.append("Pinbar detectado")
        
        # Factor 5: Volatilidad
        recent_ranges = [c.total_range for c in candles[-10:]]
        avg_range = sum(recent_ranges) / len(recent_ranges)
        current_volatility = candle.total_range / avg_range if avg_range > 0 else 1
        
        if current_volatility > 1.5:  # Alta volatilidad
            confidence += 0.1
            reasons.append("Alta volatilidad")
        
        # Generar señal solo si hay suficiente confianza
        if confidence >= 0.7 and signal_type != SignalType.WAIT:
            return Signal(
                timestamp=datetime.now(),
                symbol=self.symbol,
                signal_type=signal_type,
                confidence=min(confidence, 1.0),
                entry_price=candle.close,
                expiry_time=60,  # 1 minuto
                reason="; ".join(reasons),
                support_resistance=self._find_nearest_level(candle.close, key_levels)
            )
        
        return None
    
    def _find_nearest_level(self, price: float, levels: List[KeyLevel]) -> Optional[float]:
        """Encuentra el nivel más cercano al precio"""
        if not levels:
            return None
        
        nearest_level = min(levels, key=lambda l: abs(l.price - price))
        return nearest_level.price