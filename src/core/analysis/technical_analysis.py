from typing import List, Tuple

from core.models.models import Candle, CandlePattern, KeyLevel
import numpy as np
from datetime import datetime


class TechnicalAnalysis:
    """Servicio mejorado de análisis técnico"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calcula la Media Móvil Exponencial optimizada"""
        if len(prices) < period:
            return []
        
        ema = []
        multiplier = 2 / (period + 1)
        
        # Primera EMA es la media simple
        sma = sum(prices[:period]) / period
        ema.append(sma)
        
        # Calcular EMA para el resto
        for i in range(period, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
            ema.append(ema_value)
            
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calcula el RSI"""
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        rsi_values = []
        
        # Primera media
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # RSI suavizado
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def identify_advanced_patterns(candles: List[Candle]) -> List[Tuple[CandlePattern, int]]:
        """Identifica patrones avanzados de velas"""
        if len(candles) < 3:
            return []
        
        patterns = []
        
        for i in range(2, len(candles)):
            current = candles[i]
            previous = candles[i-1]
            before_previous = candles[i-2]
            
            # Patrón Pinbar
            if (current.total_range > 0 and 
                current.body_size / current.total_range < 0.3 and
                (current.upper_shadow > current.body_size * 2 or 
                 current.lower_shadow > current.body_size * 2)):
                patterns.append((CandlePattern.PINBAR, i))
            
            # Envolvente alcista
            if (previous.is_bearish and current.is_bullish and
                current.open < previous.close and current.close > previous.open):
                patterns.append((CandlePattern.ENGULFING_BULL, i))
            
            # Envolvente bajista
            if (previous.is_bullish and current.is_bearish and
                current.open > previous.close and current.close < previous.open):
                patterns.append((CandlePattern.ENGULFING_BEAR, i))
            
            # Martillo
            if (current.is_bullish and current.lower_shadow > current.body_size * 2 and
                current.upper_shadow < current.body_size * 0.5):
                patterns.append((CandlePattern.HAMMER, i))
        
        return patterns
    
    @staticmethod
    def find_dynamic_support_resistance(candles: List[Candle], lookback: int = 20, min_touches: int = 2) -> List[KeyLevel]:
        """Encuentra soportes y resistencias dinámicos"""
        if len(candles) < lookback:
            return []
        
        levels = []
        recent_candles = candles[-lookback:]
        
        # Agrupar precios similares
        highs = [c.high for c in recent_candles]
        lows = [c.low for c in recent_candles]
        
        # Encontrar clusters de precios
        tolerance = np.std([c.close for c in recent_candles]) * 0.5
        
        # Resistencias
        resistance_clusters = []
        for high in highs:
            cluster = [h for h in highs if abs(h - high) <= tolerance]
            if len(cluster) >= min_touches:
                avg_price = sum(cluster) / len(cluster)
                resistance_clusters.append((avg_price, len(cluster)))
        
        # Eliminar duplicados
        unique_resistances = []
        for price, count in resistance_clusters:
            if not any(abs(price - existing[0]) <= tolerance for existing in unique_resistances):
                unique_resistances.append((price, count))
        
        for price, count in unique_resistances:
            level = KeyLevel(
                price=price,
                level_type='resistance',
                strength=min(count, 5),
                touch_count=count,
                last_touch=datetime.now()
            )
            levels.append(level)
        
        # Soportes (mismo proceso)
        support_clusters = []
        for low in lows:
            cluster = [l for l in lows if abs(l - low) <= tolerance]
            if len(cluster) >= min_touches:
                avg_price = sum(cluster) / len(cluster)
                support_clusters.append((avg_price, len(cluster)))
        
        unique_supports = []
        for price, count in support_clusters:
            if not any(abs(price - existing[0]) <= tolerance for existing in unique_supports):
                unique_supports.append((price, count))
        
        for price, count in unique_supports:
            level = KeyLevel(
                price=price,
                level_type='support',
                strength=min(count, 5),
                touch_count=count,
                last_touch=datetime.now()
            )
            levels.append(level)
        
        return levels