from typing import List, Tuple, Dict
from core.models.models import Candle, CandlePattern, KeyLevel
import numpy as np
from datetime import datetime


class TechnicalAnalysis:
    """Servicio mejorado de análisis técnico para scalping"""
    
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
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Calcula Media Móvil Simple"""
        if len(prices) < period:
            return []
        
        sma = []
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma.append(avg)
        return sma
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calcula el RSI optimizado"""
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
    def calculate_stochastic(candles: List[Candle], k_period: int = 14, d_period: int = 3) -> Tuple[List[float], List[float]]:
        """Calcula oscilador estocástico"""
        if len(candles) < k_period:
            return [], []
        
        k_values = []
        
        for i in range(k_period - 1, len(candles)):
            period_candles = candles[i - k_period + 1:i + 1]
            highest_high = max(c.high for c in period_candles)
            lowest_low = min(c.low for c in period_candles)
            current_close = candles[i].close
            
            if highest_high - lowest_low == 0:
                k_values.append(50)
            else:
                k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
                k_values.append(k)
        
        # Calcular %D (media móvil de %K)
        d_values = TechnicalAnalysis.calculate_sma(k_values, d_period)
        
        return k_values, d_values
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """Calcula MACD"""
        if len(prices) < slow:
            return [], [], []
        
        ema_fast = TechnicalAnalysis.calculate_ema(prices, fast)
        ema_slow = TechnicalAnalysis.calculate_ema(prices, slow)
        
        # Ajustar longitudes
        min_length = min(len(ema_fast), len(ema_slow))
        ema_fast = ema_fast[-min_length:]
        ema_slow = ema_slow[-min_length:]
        
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(min_length)]
        signal_line = TechnicalAnalysis.calculate_ema(macd_line, signal)
        
        # Histograma
        histogram = []
        if len(signal_line) > 0:
            macd_adjusted = macd_line[-len(signal_line):]
            histogram = [macd_adjusted[i] - signal_line[i] for i in range(len(signal_line))]
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """Calcula Bandas de Bollinger"""
        if len(prices) < period:
            return [], [], []
        
        sma = TechnicalAnalysis.calculate_sma(prices, period)
        upper_band = []
        lower_band = []
        
        for i in range(len(sma)):
            price_slice = prices[i:i + period]
            std = np.std(price_slice)
            upper_band.append(sma[i] + (std_dev * std))
            lower_band.append(sma[i] - (std_dev * std))
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_atr(candles: List[Candle], period: int = 14) -> List[float]:
        """Calcula Average True Range"""
        if len(candles) < period + 1:
            return []
        
        true_ranges = []
        for i in range(1, len(candles)):
            high_low = candles[i].high - candles[i].low
            high_close_prev = abs(candles[i].high - candles[i-1].close)
            low_close_prev = abs(candles[i].low - candles[i-1].close)
            
            tr = max(high_low, high_close_prev, low_close_prev)
            true_ranges.append(tr)
        
        # ATR es una media móvil exponencial de los true ranges
        return TechnicalAnalysis.calculate_ema(true_ranges, period)
    
    @staticmethod
    def detect_price_action_patterns(candles: List[Candle]) -> List[Tuple[str, int, float]]:
        """Detecta patrones de price action para scalping"""
        if len(candles) < 5:
            return []
        
        patterns = []
        
        for i in range(4, len(candles)):
            current = candles[i]
            prev1 = candles[i-1]
            prev2 = candles[i-2]
            prev3 = candles[i-3]
            prev4 = candles[i-4]
            
            # Break of Structure (BOS)
            if TechnicalAnalysis._is_break_of_structure(candles[i-4:i+1]):
                direction = "bullish" if current.close > prev2.high else "bearish"
                patterns.append((f"BOS_{direction}", i, 0.8))
            
            # Change of Character (CHoCH)
            if TechnicalAnalysis._is_change_of_character(candles[i-4:i+1]):
                direction = "bullish" if current.close > current.open else "bearish"
                patterns.append((f"CHOCH_{direction}", i, 0.9))
            
            # Liquidity Grab
            if TechnicalAnalysis._is_liquidity_grab(candles[i-3:i+1]):
                direction = "bullish" if current.close > prev1.close else "bearish"
                patterns.append((f"LIQUIDITY_GRAB_{direction}", i, 0.7))
            
            # Fair Value Gap (FVG)
            if TechnicalAnalysis._is_fair_value_gap(candles[i-2:i+1]):
                patterns.append(("FVG", i, 0.6))
        
        return patterns
    
    @staticmethod
    def _is_break_of_structure(candles: List[Candle]) -> bool:
        """Detecta ruptura de estructura"""
        if len(candles) < 5:
            return False
        
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        # BOS alcista: nuevo máximo después de secuencia bajista
        recent_high = max(highs[-2:])
        prev_high = max(highs[:-2])
        
        # BOS bajista: nuevo mínimo después de secuencia alcista
        recent_low = min(lows[-2:])
        prev_low = min(lows[:-2])
        
        return recent_high > prev_high or recent_low < prev_low
    
    @staticmethod
    def _is_change_of_character(candles: List[Candle]) -> bool:
        """Detecta cambio de carácter del mercado"""
        if len(candles) < 5:
            return False
        
        # Analizar la secuencia de velas para detectar cambio de dirección
        closes = [c.close for c in candles]
        
        # Tendencia previa
        early_trend = closes[2] - closes[0]
        recent_trend = closes[-1] - closes[-3]
        
        # CHoCH cuando la tendencia cambia significativamente
        return (early_trend > 0 and recent_trend < 0) or (early_trend < 0 and recent_trend > 0)
    
    @staticmethod
    def _is_liquidity_grab(candles: List[Candle]) -> bool:
        """Detecta toma de liquidez"""
        if len(candles) < 4:
            return False
        
        # Buscar spike temporal seguido de reversión
        spike_candle = candles[-2]
        current = candles[-1]
        prev = candles[-3]
        
        # Liquidity grab alcista
        if (spike_candle.low < prev.low and 
            current.close > spike_candle.open and
            spike_candle.lower_shadow > spike_candle.body_size):
            return True
        
        # Liquidity grab bajista
        if (spike_candle.high > prev.high and 
            current.close < spike_candle.open and
            spike_candle.upper_shadow > spike_candle.body_size):
            return True
        
        return False
    
    @staticmethod
    def _is_fair_value_gap(candles: List[Candle]) -> bool:
        """Detecta Fair Value Gap"""
        if len(candles) < 3:
            return False
        
        candle1, candle2, candle3 = candles[-3], candles[-2], candles[-1]
        
        # FVG alcista: gap entre low de candle3 y high de candle1
        bullish_gap = candle3.low > candle1.high
        
        # FVG bajista: gap entre high de candle3 y low de candle1
        bearish_gap = candle3.high < candle1.low
        
        return bullish_gap or bearish_gap
    
    @staticmethod
    def identify_advanced_patterns(candles: List[Candle]) -> List[Tuple[CandlePattern, int]]:
        """Identifica patrones avanzados de velas mejorado"""
        if len(candles) < 3:
            return []
        
        patterns = []
        
        for i in range(2, len(candles)):
            current = candles[i]
            previous = candles[i-1]
            before_previous = candles[i-2]
            
            # Patrón Pinbar mejorado
            if TechnicalAnalysis._is_enhanced_pinbar(current):
                patterns.append((CandlePattern.PINBAR, i))
            
            # Envolvente alcista
            if (previous.is_bearish and current.is_bullish and
                current.open < previous.close and current.close > previous.open and
                current.body_size > previous.body_size * 1.5):
                patterns.append((CandlePattern.ENGULFING_BULL, i))
            
            # Envolvente bajista
            if (previous.is_bullish and current.is_bearish and
                current.open > previous.close and current.close < previous.open and
                current.body_size > previous.body_size * 1.5):
                patterns.append((CandlePattern.ENGULFING_BEAR, i))
            
            # Martillo mejorado
            if TechnicalAnalysis._is_enhanced_hammer(current):
                patterns.append((CandlePattern.HAMMER, i))
            
            # Shooting Star mejorado
            if TechnicalAnalysis._is_enhanced_shooting_star(current):
                patterns.append((CandlePattern.SHOOTING_STAR, i))
            
            # Doji mejorado
            if TechnicalAnalysis._is_enhanced_doji(current):
                patterns.append((CandlePattern.DOJI, i))
        
        return patterns
    
    @staticmethod
    def _is_enhanced_pinbar(candle: Candle) -> bool:
        """Detecta pinbar mejorado"""
        if candle.total_range == 0:
            return False
        
        body_ratio = candle.body_size / candle.total_range
        shadow_ratio = max(candle.upper_shadow, candle.lower_shadow) / candle.total_range
        
        return (body_ratio < 0.25 and shadow_ratio > 0.6)
    
    @staticmethod
    def _is_enhanced_hammer(candle: Candle) -> bool:
        """Detecta martillo mejorado"""
        if candle.total_range == 0:
            return False
        
        return (candle.lower_shadow > candle.body_size * 2 and
                candle.upper_shadow < candle.body_size * 0.3 and
                candle.body_size > candle.total_range * 0.2)
    
    @staticmethod
    def _is_enhanced_shooting_star(candle: Candle) -> bool:
        """Detecta shooting star mejorado"""
        if candle.total_range == 0:
            return False
        
        return (candle.upper_shadow > candle.body_size * 2 and
                candle.lower_shadow < candle.body_size * 0.3 and
                candle.body_size > candle.total_range * 0.2)
    
    @staticmethod
    def _is_enhanced_doji(candle: Candle) -> bool:
        """Detecta doji mejorado"""
        if candle.total_range == 0:
            return False
        
        body_ratio = candle.body_size / candle.total_range
        return body_ratio < 0.05 and candle.total_range > 0
    
    @staticmethod
    def find_dynamic_support_resistance(candles: List[Candle], lookback: int = 20, min_touches: int = 2) -> List[KeyLevel]:
        """Encuentra soportes y resistencias dinámicos mejorado"""
        if len(candles) < lookback:
            return []
        
        levels = []
        recent_candles = candles[-lookback:]
        
        # Usar pivots en lugar de solo highs/lows
        pivot_highs = TechnicalAnalysis._find_pivot_points(recent_candles, 'high')
        pivot_lows = TechnicalAnalysis._find_pivot_points(recent_candles, 'low')
        
        # Agrupar precios similares con tolerancia adaptativa
        price_range = max(c.high for c in recent_candles) - min(c.low for c in recent_candles)
        tolerance = price_range * 0.002  # 0.2% del rango
        
        # Procesar resistencias
        levels.extend(TechnicalAnalysis._process_levels(pivot_highs, tolerance, 'resistance', min_touches))
        
        # Procesar soportes
        levels.extend(TechnicalAnalysis._process_levels(pivot_lows, tolerance, 'support', min_touches))
        
        return levels
    
    @staticmethod
    def _find_pivot_points(candles: List[Candle], type_point: str, window: int = 3) -> List[float]:
        """Encuentra puntos pivot"""
        pivots = []
        
        for i in range(window, len(candles) - window):
            if type_point == 'high':
                current_value = candles[i].high
                is_pivot = all(current_value >= candles[j].high for j in range(i-window, i+window+1))
            else:
                current_value = candles[i].low
                is_pivot = all(current_value <= candles[j].low for j in range(i-window, i+window+1))
            
            if is_pivot:
                pivots.append(current_value)
        
        return pivots
    
    @staticmethod
    def _process_levels(prices: List[float], tolerance: float, level_type: str, min_touches: int) -> List[KeyLevel]:
        """Procesa niveles de soporte/resistencia"""
        levels = []
        processed_prices = set()
        
        for price in prices:
            if price in processed_prices:
                continue
            
            # Encontrar precios similares
            cluster = [p for p in prices if abs(p - price) <= tolerance]
            
            if len(cluster) >= min_touches:
                avg_price = sum(cluster) / len(cluster)
                strength = min(len(cluster), 5)
                
                level = KeyLevel(
                    price=avg_price,
                    level_type=level_type,
                    strength=strength,
                    touch_count=len(cluster),
                    last_touch=datetime.now()
                )
                levels.append(level)
                
                # Marcar precios como procesados
                processed_prices.update(cluster)
        
        return levels
    
    @staticmethod
    def calculate_market_structure(candles: List[Candle]) -> Dict[str, any]:
        """Analiza estructura del mercado"""
        if len(candles) < 10:
            return {}
        
        # Calcular swing points
        swing_highs = TechnicalAnalysis._find_pivot_points(candles, 'high', 2)
        swing_lows = TechnicalAnalysis._find_pivot_points(candles, 'low', 2)
        
        # Determinar tendencia
        trend = TechnicalAnalysis._determine_trend(swing_highs, swing_lows)
        
        # Calcular volatilidad
        ranges = [c.total_range for c in candles[-10:]]
        avg_range = sum(ranges) / len(ranges)
        current_volatility = candles[-1].total_range / avg_range if avg_range > 0 else 1
        
        return {
            'trend': trend,
            'volatility': current_volatility,
            'swing_highs_count': len(swing_highs),
            'swing_lows_count': len(swing_lows),
            'structure_strength': len(swing_highs) + len(swing_lows)
        }
    
    @staticmethod
    def _determine_trend(swing_highs: List[float], swing_lows: List[float]) -> str:
        """Determina la tendencia basada en swing points"""
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'sideways'
        
        # Analizar últimos swings
        recent_highs = swing_highs[-2:]
        recent_lows = swing_lows[-2:]
        
        higher_highs = recent_highs[1] > recent_highs[0]
        higher_lows = recent_lows[1] > recent_lows[0]
        lower_highs = recent_highs[1] < recent_highs[0]
        lower_lows = recent_lows[1] < recent_lows[0]
        
        if higher_highs and higher_lows:
            return 'uptrend'
        elif lower_highs and lower_lows:
            return 'downtrend'
        else:
            return 'sideways'