from typing import List, Optional, Tuple, Dict
from core.analysis.technical_analysis import TechnicalAnalysis
from core.models.models import Candle, CandlePattern, KeyLevel, Signal, SignalType
from datetime import datetime
import logging
import time


class RealTimeScalpingStrategy:
    """Estrategia avanzada de scalping optimizada para opciones binarias 1min"""
    
    def __init__(self):
        self.technical_analysis = TechnicalAnalysis()
        self.logger = logging.getLogger(__name__)
        self.last_signal_time = 0
        self.min_signal_interval = 20  # Reducido a 20 segundos para más señales
        self.symbol = ""
        
        # Configuración de filtros
        self.min_confidence = 0.65  # Reducido para más señales
        self.volatility_threshold = 0.5  # Filtro de volatilidad mínima
        
        # Cache para indicadores
        self._indicator_cache = {}
        self._cache_time = 0
        
    def analyze_real_time(self, candles: List[Candle], symbol: str) -> Optional[Signal]:
        """Análisis en tiempo real optimizado con múltiples estrategias"""
        if len(candles) < 50:  # Necesitamos más historia para indicadores
            return None
        
        self.symbol = symbol
        
        # Control de frecuencia de señales
        current_time = time.time()
        if current_time - self.last_signal_time < self.min_signal_interval:
            return None
        
        # Actualizar cache de indicadores
        self._update_indicator_cache(candles)
        
        # Análisis multi-estrategia
        signals = []
        
        # Estrategia 1: Price Action + Momentum
        pa_signal = self._price_action_momentum_strategy(candles)
        if pa_signal:
            signals.append(pa_signal)
        
        # Estrategia 2: Mean Reversion
        mr_signal = self._mean_reversion_strategy(candles)
        if mr_signal:
            signals.append(mr_signal)
        
        # Estrategia 3: Breakout
        bo_signal = self._breakout_strategy(candles)
        if bo_signal:
            signals.append(bo_signal)
        
        # Estrategia 4: Confluence Trading
        conf_signal = self._confluence_strategy(candles)
        if conf_signal:
            signals.append(conf_signal)
        
        # Seleccionar la mejor señal
        if signals:
            best_signal = max(signals, key=lambda s: s.confidence)
            if best_signal.confidence >= self.min_confidence:
                self.last_signal_time = current_time
                return best_signal
        
        return None
    
    def _update_indicator_cache(self, candles: List[Candle]):
        """Actualiza cache de indicadores para optimizar performance"""
        current_time = time.time()
        
        # Solo actualizar si han pasado al menos 5 segundos
        if current_time - self._cache_time < 5:
            return
        
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        # Medias móviles
        self._indicator_cache['ema9'] = self.technical_analysis.calculate_ema(closes, 9)
        self._indicator_cache['ema21'] = self.technical_analysis.calculate_ema(closes, 21)
        self._indicator_cache['ema50'] = self.technical_analysis.calculate_ema(closes, 50)
        self._indicator_cache['sma20'] = self.technical_analysis.calculate_sma(closes, 20)
        
        # Osciladores
        self._indicator_cache['rsi'] = self.technical_analysis.calculate_rsi(closes, 14)
        self._indicator_cache['rsi_fast'] = self.technical_analysis.calculate_rsi(closes, 5)
        
        # Estocástico
        stoch_k, stoch_d = self.technical_analysis.calculate_stochastic(candles, 14, 3)
        self._indicator_cache['stoch_k'] = stoch_k
        self._indicator_cache['stoch_d'] = stoch_d
        
        # MACD
        macd, signal, histogram = self.technical_analysis.calculate_macd(closes)
        self._indicator_cache['macd'] = macd
        self._indicator_cache['macd_signal'] = signal
        self._indicator_cache['macd_histogram'] = histogram
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.technical_analysis.calculate_bollinger_bands(closes)
        self._indicator_cache['bb_upper'] = bb_upper
        self._indicator_cache['bb_middle'] = bb_middle
        self._indicator_cache['bb_lower'] = bb_lower
        
        # ATR para volatilidad
        self._indicator_cache['atr'] = self.technical_analysis.calculate_atr(candles)
        
        # Price Action Patterns
        self._indicator_cache['pa_patterns'] = self.technical_analysis.detect_price_action_patterns(candles)
        
        # Estructura del mercado
        self._indicator_cache['market_structure'] = self.technical_analysis.calculate_market_structure(candles)
        
        # Niveles clave
        self._indicator_cache['key_levels'] = self.technical_analysis.find_dynamic_support_resistance(candles, 30, 2)
        
        # Patrones de velas
        self._indicator_cache['candle_patterns'] = self.technical_analysis.identify_advanced_patterns(candles[-10:])
        
        self._cache_time = current_time
    
    def _price_action_momentum_strategy(self, candles: List[Candle]) -> Optional[Signal]:
        """Estrategia basada en price action y momentum"""
        current_candle = candles[-1]
        
        # Obtener indicadores del cache
        pa_patterns = self._indicator_cache.get('pa_patterns', [])
        rsi = self._indicator_cache.get('rsi', [])
        ema9 = self._indicator_cache.get('ema9', [])
        ema21 = self._indicator_cache.get('ema21', [])
        
        if not all([rsi, ema9, ema21]):
            return None
        
        confidence = 0.0
        reasons = []
        signal_type = SignalType.WAIT
        
        # Análisis de price action patterns
        recent_patterns = [p for p in pa_patterns if p[1] >= len(candles) - 3]
        
        for pattern_name, index, pattern_confidence in recent_patterns:
            confidence += pattern_confidence * 0.3
            reasons.append(f"Patrón: {pattern_name}")
            
            if "bullish" in pattern_name.lower() or "BOS_bullish" in pattern_name:
                signal_type = SignalType.CALL
            elif "bearish" in pattern_name.lower() or "BOS_bearish" in pattern_name:
                signal_type = SignalType.PUT
        
        # Momentum con EMAs
        current_ema9 = ema9[-1]
        current_ema21 = ema21[-1]
        
        if current_candle.close > current_ema9 > current_ema21:
            confidence += 0.25
            reasons.append("EMA bullish alignment")
            if signal_type == SignalType.WAIT:
                signal_type = SignalType.CALL
        elif current_candle.close < current_ema9 < current_ema21:
            confidence += 0.25
            reasons.append("EMA bearish alignment")
            if signal_type == SignalType.WAIT:
                signal_type = SignalType.PUT
        
        # RSI momentum
        current_rsi = rsi[-1]
        if len(rsi) >= 2:
            rsi_momentum = rsi[-1] - rsi[-2]
            
            if current_rsi < 35 and rsi_momentum > 2:
                confidence += 0.2
                reasons.append("RSI bullish divergence")
                if signal_type == SignalType.WAIT:
                    signal_type = SignalType.CALL
            elif current_rsi > 65 and rsi_momentum < -2:
                confidence += 0.2
                reasons.append("RSI bearish divergence")
                if signal_type == SignalType.WAIT:
                    signal_type = SignalType.PUT
        
        if confidence >= 0.6 and signal_type != SignalType.WAIT:
            return self._create_signal(signal_type, confidence, current_candle.close, reasons)
        
        return None
    
    def _mean_reversion_strategy(self, candles: List[Candle]) -> Optional[Signal]:
        """Estrategia de reversión a la media"""
        current_candle = candles[-1]
        
        # Obtener indicadores
        bb_upper = self._indicator_cache.get('bb_upper', [])
        bb_lower = self._indicator_cache.get('bb_lower', [])
        bb_middle = self._indicator_cache.get('bb_middle', [])
        rsi = self._indicator_cache.get('rsi', [])
        stoch_k = self._indicator_cache.get('stoch_k', [])
        
        if not all([bb_upper, bb_lower, bb_middle, rsi, stoch_k]):
            return None
        
        confidence = 0.0
        reasons = []
        signal_type = SignalType.WAIT
        
        current_price = current_candle.close
        current_bb_upper = bb_upper[-1]
        current_bb_lower = bb_lower[-1]
        current_bb_middle = bb_middle[-1]
        current_rsi = rsi[-1]
        current_stoch = stoch_k[-1]
        
        # Señal de reversión alcista desde sobrevendido
        if (current_price <= current_bb_lower and 
            current_rsi < 30 and 
            current_stoch < 20):
            
            confidence += 0.4
            reasons.append("Sobrevendido múltiple")
            signal_type = SignalType.CALL
            
            # Confirmación adicional con velas
            if current_candle.is_bullish and current_candle.body_size > current_candle.total_range * 0.6:
                confidence += 0.3
                reasons.append("Vela de reversión alcista")
        
        # Señal de reversión bajista desde sobrecomprado
        elif (current_price >= current_bb_upper and 
              current_rsi > 70 and 
              current_stoch > 80):
            
            confidence += 0.4
            reasons.append("Sobrecomprado múltiple")
            signal_type = SignalType.PUT
            
            # Confirmación adicional con velas
            if current_candle.is_bearish and current_candle.body_size > current_candle.total_range * 0.6:
                confidence += 0.3
                reasons.append("Vela de reversión bajista")
        
        # Squeeze de Bollinger (baja volatilidad seguida de expansión)
        if len(bb_upper) >= 5:
            bb_width_current = (current_bb_upper - current_bb_lower) / current_bb_middle
            bb_width_avg = sum([(bb_upper[i] - bb_lower[i]) / bb_middle[i] 
                               for i in range(-5, -1)]) / 4
            
            if bb_width_current > bb_width_avg * 1.5:
                confidence += 0.2
                reasons.append("Expansión de volatilidad")
        
        if confidence >= 0.6 and signal_type != SignalType.WAIT:
            return self._create_signal(signal_type, confidence, current_candle.close, reasons)
        
        return None
    
    def _breakout_strategy(self, candles: List[Candle]) -> Optional[Signal]:
        """Estrategia de ruptura de niveles clave"""
        current_candle = candles[-1]
        
        # Obtener niveles clave
        key_levels = self._indicator_cache.get('key_levels', [])
        ema21 = self._indicator_cache.get('ema21', [])
        atr = self._indicator_cache.get('atr', [])
        
        if not all([key_levels, ema21, atr]):
            return None
        
        confidence = 0.0
        reasons = []
        signal_type = SignalType.WAIT
        
        current_price = current_candle.close
        current_ema21 = ema21[-1]
        current_atr = atr[-1]
        
        # Buscar ruptura de niveles importantes
        for level in key_levels:
            distance_to_level = abs(current_price - level.price) / current_price
            
            # Ruptura de resistencia (señal CALL)
            if (level.level_type == 'resistance' and 
                current_price > level.price and 
                distance_to_level < 0.001 and  # Ruptura reciente
                current_candle.volume > 0):
                
                confidence += 0.3 * (level.strength / 5)
                reasons.append(f"Ruptura resistencia {level.price:.5f}")
                signal_type = SignalType.CALL
                
                # Confirmación con tendencia
                if current_price > current_ema21:
                    confidence += 0.2
                    reasons.append("Ruptura en tendencia alcista")
                
                # Confirmación con volumen y volatilidad
                if current_candle.total_range > current_atr * 1.5:
                    confidence += 0.2
                    reasons.append("Ruptura con alta volatilidad")
            
            # Ruptura de soporte (señal PUT)
            elif (level.level_type == 'support' and 
                  current_price < level.price and 
                  distance_to_level < 0.001 and
                  current_candle.volume > 0):
                
                confidence += 0.3 * (level.strength / 5)
                reasons.append(f"Ruptura soporte {level.price:.5f}")
                signal_type = SignalType.PUT
                
                # Confirmación con tendencia
                if current_price < current_ema21:
                    confidence += 0.2
                    reasons.append("Ruptura en tendencia bajista")
                
                # Confirmación con volumen y volatilidad
                if current_candle.total_range > current_atr * 1.5:
                    confidence += 0.2
                    reasons.append("Ruptura con alta volatilidad")
        
        if confidence >= 0.6 and signal_type != SignalType.WAIT:
            return self._create_signal(signal_type, confidence, current_candle.close, reasons)
        
        return None
    
    def _confluence_strategy(self, candles: List[Candle]) -> Optional[Signal]:
        """Estrategia de confluencia múltiple"""
        current_candle = candles[-1]
        
        # Obtener todos los indicadores
        macd = self._indicator_cache.get('macd', [])
        macd_signal = self._indicator_cache.get('macd_signal', [])
        macd_histogram = self._indicator_cache.get('macd_histogram', [])
        rsi_fast = self._indicator_cache.get('rsi_fast', [])
        stoch_k = self._indicator_cache.get('stoch_k', [])
        stoch_d = self._indicator_cache.get('stoch_d', [])
        ema9 = self._indicator_cache.get('ema9', [])
        ema50 = self._indicator_cache.get('ema50', [])
        candle_patterns = self._indicator_cache.get('candle_patterns', [])
        market_structure = self._indicator_cache.get('market_structure', {})
        
        if not all([macd, macd_signal, rsi_fast, stoch_k, ema9, ema50]):
            return None
        
        confluence_score = 0
        reasons = []
        signal_type = SignalType.WAIT
        bullish_signals = 0
        bearish_signals = 0
        
        # 1. MACD Analysis
        if len(macd) >= 2 and len(macd_signal) >= 2:
            if macd[-1] > macd_signal[-1] and macd[-2] <= macd_signal[-2]:
                bullish_signals += 1
                reasons.append("MACD bullish crossover")
            elif macd[-1] < macd_signal[-1] and macd[-2] >= macd_signal[-2]:
                bearish_signals += 1
                reasons.append("MACD bearish crossover")
        
        # 2. RSI Fast momentum
        if len(rsi_fast) >= 2:
            rsi_momentum = rsi_fast[-1] - rsi_fast[-2]
            if rsi_fast[-1] < 70 and rsi_momentum > 3:
                bullish_signals += 1
                reasons.append("RSI fast bullish momentum")
            elif rsi_fast[-1] > 30 and rsi_momentum < -3:
                bearish_signals += 1
                reasons.append("RSI fast bearish momentum")
        
        # 3. Stochastic crossover
        if len(stoch_k) >= 2 and len(stoch_d) >= 2:
            if (stoch_k[-1] > stoch_d[-1] and stoch_k[-2] <= stoch_d[-2] and 
                stoch_k[-1] < 80):
                bullish_signals += 1
                reasons.append("Stochastic bullish crossover")
            elif (stoch_k[-1] < stoch_d[-1] and stoch_k[-2] >= stoch_d[-2] and 
                  stoch_k[-1] > 20):
                bearish_signals += 1
                reasons.append("Stochastic bearish crossover")
        
        # 4. EMA trend alignment
        current_ema9 = ema9[-1]
        current_ema50 = ema50[-1]
        
        if current_candle.close > current_ema9 > current_ema50:
            bullish_signals += 1
            reasons.append("EMA trend bullish")
        elif current_candle.close < current_ema9 < current_ema50:
            bearish_signals += 1
            reasons.append("EMA trend bearish")
        
        # 5. Candle patterns
        recent_patterns = [p for p in candle_patterns if p[1] >= len(candles) - 2]
        for pattern, index in recent_patterns:
            if pattern in [CandlePattern.HAMMER, CandlePattern.ENGULFING_BULL]:
                bullish_signals += 1
                reasons.append(f"Bullish pattern: {pattern.value}")
            elif pattern in [CandlePattern.SHOOTING_STAR, CandlePattern.ENGULFING_BEAR]:
                bearish_signals += 1
                reasons.append(f"Bearish pattern: {pattern.value}")
        
        # 6. Market structure
        trend = market_structure.get('trend', 'sideways')
        if trend == 'uptrend':
            bullish_signals += 1
            reasons.append("Market structure bullish")
        elif trend == 'downtrend':
            bearish_signals += 1
            reasons.append("Market structure bearish")
        
        # Determinar señal basada en confluencia
        total_signals = bullish_signals + bearish_signals
        
        if bullish_signals >= 3 and bullish_signals > bearish_signals:
            signal_type = SignalType.CALL
            confluence_score = min(bullish_signals / 6, 1.0)
        elif bearish_signals >= 3 and bearish_signals > bullish_signals:
            signal_type = SignalType.PUT
            confluence_score = min(bearish_signals / 6, 1.0)
        
        # Bonus por alta confluencia
        if total_signals >= 5:
            confluence_score += 0.1
            reasons.append("High confluence setup")
        
        if confluence_score >= 0.6 and signal_type != SignalType.WAIT:
            return self._create_signal(signal_type, confluence_score, current_candle.close, reasons)
        
        return None
    
    def _create_signal(self, signal_type: SignalType, confidence: float, entry_price: float, 
                      reasons: List[str]) -> Signal:
        """Crea objeto Signal con configuración optimizada"""
        
        # Determinar tiempo de expiración basado en volatilidad
        atr = self._indicator_cache.get('atr', [])
        market_structure = self._indicator_cache.get('market_structure', {})
        
        volatility = market_structure.get('volatility', 1.0)
        
        # Tiempo de expiración adaptativo
        if volatility > 1.5:
            expiry = 60  # 1 minuto para alta volatilidad
        elif volatility > 1.0:
            expiry = 120  # 2 minutos para volatilidad media
        else:
            expiry = 180  # 3 minutos para baja volatilidad
        
        # Calcular stop loss y take profit estimados
        if atr:
            current_atr = atr[-1]
            stop_loss = entry_price - (current_atr * 1.5) if signal_type == SignalType.CALL else entry_price + (current_atr * 1.5)
            take_profit = entry_price + (current_atr * 2) if signal_type == SignalType.CALL else entry_price - (current_atr * 2)
        else:
            stop_loss = None
            take_profit = None
        
        # Buscar nivel de soporte/resistencia más cercano
        key_levels = self._indicator_cache.get('key_levels', [])
        support_resistance = self._find_nearest_level(entry_price, key_levels)
        
        return Signal(
            timestamp=datetime.now(),
            symbol=self.symbol,
            signal_type=signal_type,
            confidence=min(confidence, 1.0),
            entry_price=entry_price,
            expiry_time=expiry,
            reason="; ".join(reasons),
            support_resistance=support_resistance,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def _find_nearest_level(self, price: float, levels: List[KeyLevel]) -> Optional[float]:
        """Encuentra el nivel más cercano al precio"""
        if not levels:
            return None
        
        nearest_level = min(levels, key=lambda l: abs(l.price - price))
        return nearest_level.price
    
    def _validate_signal_conditions(self, candles: List[Candle]) -> bool:
        """Valida condiciones generales del mercado antes de generar señal"""
        
        # Filtro de volatilidad mínima
        if len(candles) >= 10:
            recent_ranges = [c.total_range for c in candles[-10:]]
            avg_range = sum(recent_ranges) / len(recent_ranges)
            current_volatility = candles[-1].total_range / avg_range if avg_range > 0 else 1
            
            if current_volatility < self.volatility_threshold:
                return False
        
        # Filtro de spread (para datos con bid/ask)
        # Este filtro se puede implementar si se tienen datos de spread
        
        # Filtro de horario de trading (evitar noticias importantes)
        current_hour = datetime.now().hour
        if current_hour in [0, 1, 2, 3, 4, 5]:  # Evitar horas de baja liquidez
            return False
        
        return True
    
    def get_strategy_status(self) -> Dict:
        """Retorna estado actual de la estrategia"""
        return {
            'last_signal_time': self.last_signal_time,
            'min_signal_interval': self.min_signal_interval,
            'min_confidence': self.min_confidence,
            'volatility_threshold': self.volatility_threshold,
            'cache_indicators': list(self._indicator_cache.keys()),
            'cache_last_update': self._cache_time
        }