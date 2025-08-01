# ================================
# CONFIGURACIÓN PRINCIPAL MEJORADA
# ================================

from typing import Dict, Any

# Configuración optimizada para diferentes fuentes de datos
BINANCE_OPTIMIZED_CONFIG = {
    'data_source': 'binance',
    'symbol': 'BTCUSDT',  # Bitcoin/USDT - Par más líquido
    'interval': '1m',
    'credentials': {},
    
    # Configuración de estrategia
    'strategy_config': {
        'min_confidence': 0.65,  # Reducido para más señales
        'min_signal_interval': 20,  # 20 segundos entre señales
        'volatility_threshold': 0.5,
        'enable_multiple_strategies': True,
        'max_signals_per_hour': 15
    },
    
    # Configuración de filtros
    'filters': {
        'enable_trend_filter': True,
        'enable_volatility_filter': True,
        'enable_session_filter': True,
        'enable_confluence_filter': True
    },
    
    # Configuración de alertas
    'alerts': {
        'min_confidence_for_high_priority': 0.80,
        'min_confidence_for_medium_priority': 0.65,
        'enable_duplicate_filter': True,
        'duplicate_timeout': 25
    }
}

FOREX_OPTIMIZED_CONFIG = {
    'data_source': 'alphavantage',
    'symbol': 'EUR/USD',  # Par más popular
    'interval': '1min',
    'credentials': {
        'api_key': '9Q5ZV1NEBFQQZ76L'
    },
    
    'strategy_config': {
        'min_confidence': 0.70,  # Forex requiere más confianza
        'min_signal_interval': 30,
        'volatility_threshold': 0.3,  # Forex menos volátil
        'enable_multiple_strategies': True,
        'max_signals_per_hour': 10
    },
    
    'filters': {
        'enable_trend_filter': True,
        'enable_volatility_filter': True,
        'enable_session_filter': True,  # Importante para forex
        'enable_confluence_filter': True
    },
    
    'alerts': {
        'min_confidence_for_high_priority': 0.85,
        'min_confidence_for_medium_priority': 0.70,
        'enable_duplicate_filter': True,
        'duplicate_timeout': 40
    }
}

STOCK_OPTIMIZED_CONFIG = {
    'data_source': 'iex',
    'symbol': 'AAPL',  # Apple - Acción líquida
    'interval': '1m',
    'credentials': {
        'api_token': 'TU_TOKEN_IEX_CLOUD'
    },
    
    'strategy_config': {
        'min_confidence': 0.75,  # Acciones más conservadoras
        'min_signal_interval': 45,
        'volatility_threshold': 0.4,
        'enable_multiple_strategies': True,
        'max_signals_per_hour': 8
    },
    
    'filters': {
        'enable_trend_filter': True,
        'enable_volatility_filter': True,
        'enable_session_filter': True,
        'enable_confluence_filter': True
    },
    
    'alerts': {
        'min_confidence_for_high_priority': 0.85,
        'min_confidence_for_medium_priority': 0.75,
        'enable_duplicate_filter': True,
        'duplicate_timeout': 60
    }
}

# Configuración optimizada para IQ Options (Opciones Binarias)
IQ_OPTIONS_OPTIMIZED_CONFIG = {
    'data_source': 'iqoptions',
    'symbol': 'EURUSD-OTC',  # Par OTC para trading 24/7
    'interval': 60,  # 1 minuto
    'credentials': {
        'email': 'trader.iqoptions@gmail.com',
        'password': 'porunbeso99'
    },
    
    # Configuración específica para opciones binarias
    'strategy_config': {
        'min_confidence': 0.60,  # Más agresivo para opciones binarias
        'min_signal_interval': 15,  # Señales más frecuentes
        'volatility_threshold': 0.4,
        'enable_multiple_strategies': True,
        'max_signals_per_hour': 20,  # Más señales por hora
        
        # Configuraciones específicas para scalping 1min
        'enable_price_action_patterns': True,
        'enable_smart_money_concepts': True,
        'enable_liquidity_grabs': True,
        'enable_fair_value_gaps': True
    },
    
    'filters': {
        'enable_trend_filter': False,  # Menos restrictivo para scalping
        'enable_volatility_filter': True,
        'enable_session_filter': False,  # OTC opera 24/7
        'enable_confluence_filter': True
    },
    
    # Configuración de expiración adaptativa
    'expiry_config': {
        'base_expiry': 60,  # 1 minuto base
        'volatility_adjustment': True,
        'trend_adjustment': True,
        'min_expiry': 60,
        'max_expiry': 300  # 5 minutos máximo
    },
    
    'alerts': {
        'min_confidence_for_high_priority': 0.75,
        'min_confidence_for_medium_priority': 0.60,
        'enable_duplicate_filter': True,
        'duplicate_timeout': 20  # Más corto para scalping
    },
    
    # Configuración de indicadores optimizada para scalping
    'indicators_config': {
        'ema_periods': [9, 21, 50],
        'rsi_periods': [5, 14],  # RSI rápido y estándar
        'stochastic_config': {'k_period': 14, 'd_period': 3},
        'macd_config': {'fast': 12, 'slow': 26, 'signal': 9},
        'bollinger_config': {'period': 20, 'std_dev': 2},
        'atr_period': 14
    }
}

# Configuración avanzada del sistema
SYSTEM_CONFIG = {
    # Buffer de datos
    'max_buffer_size': 500,
    'min_history_for_analysis': 50,
    'historical_data_depth': 400,
    
    # Rendimiento
    'enable_performance_monitoring': True,
    'enable_data_quality_monitoring': True,
    'performance_report_interval': 300,  # 5 minutos
    
    # Logging
    'log_level': 'INFO',
    'enable_detailed_logging': True,
    'log_signal_details': True,
    
    # WebSocket
    'websocket_config': {
        'host': 'localhost',
        'port': 8765,
        'enable_real_time_broadcast': True
    },
    
    # Base de datos (opcional)
    'database_config': {
        'enabled': False,
        'type': 'sqlite',
        'path': 'trading_data.db'
    }
}

# Configuraciones específicas por tipo de trading
SCALPING_1MIN_CONFIG = {
    'trading_style': 'scalping_1min',
    'target_timeframe': '1m',
    'expected_signals_per_hour': 10-20,
    'win_rate_target': 0.65,
    'risk_reward_ratio': 1.2,
    
    'strategy_weights': {
        'price_action_momentum': 0.30,
        'mean_reversion': 0.25,
        'breakout': 0.25,
        'confluence': 0.20
    },
    
    'indicators_priority': [
        'ema_crossovers',
        'rsi_divergence',
        'price_action_patterns',
        'support_resistance_levels',
        'volatility_breakouts'
    ]
}

# Configuración de notificaciones externas
NOTIFICATION_CONFIG = {
    'telegram': {
        'enabled': False,
        'bot_token': '',
        'chat_id': '',
        'message_format': 'detailed'
    },
    
    'discord': {
        'enabled': False,
        'webhook_url': '',
        'message_format': 'compact'
    },
    
    'email': {
        'enabled': False,
        'smtp_server': '',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'to_email': ''
    },
    
    'webhook': {
        'enabled': False,
        'url': '',
        'headers': {},
        'format': 'json'
    }
}

# Funciones de configuración
def get_optimized_config(data_source: str) -> Dict[str, Any]:
    """Obtiene configuración optimizada según la fuente de datos"""
    
    configs = {
        'binance': BINANCE_OPTIMIZED_CONFIG,
        'alphavantage': FOREX_OPTIMIZED_CONFIG,
        'iex': STOCK_OPTIMIZED_CONFIG,
        'iqoptions': IQ_OPTIONS_OPTIMIZED_CONFIG
    }
    
    if data_source not in configs:
        raise ValueError(f"Fuente de datos no soportada: {data_source}")
    
    # Combinar con configuración del sistema
    config = configs[data_source].copy()
    config['system'] = SYSTEM_CONFIG
    config['notifications'] = NOTIFICATION_CONFIG
    config['scalping'] = SCALPING_1MIN_CONFIG
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """Valida la configuración del sistema"""
    
    required_fields = ['data_source', 'symbol', 'credentials']
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    # Validar credenciales según fuente
    data_source = config['data_source']
    credentials = config['credentials']
    
    if data_source == 'alphavantage' and not credentials.get('api_key'):
        raise ValueError("API key requerida para Alpha Vantage")
    
    if data_source == 'iex' and not credentials.get('api_token'):
        raise ValueError("API token requerido para IEX Cloud")
    
    if data_source == 'iqoptions':
        if not credentials.get('email') or not credentials.get('password'):
            raise ValueError("Email y password requeridos para IQ Options")
    
    return True

def create_custom_config(base_config: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Crea configuración personalizada basada en una base"""
    
    config = get_optimized_config(base_config)
    
    # Aplicar overrides de forma recursiva
    def deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict:
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    deep_update(config, overrides)
    
    # Validar configuración resultante
    validate_config(config)
    
    return config

# Configuraciones predefinidas para diferentes escenarios
AGGRESSIVE_SCALPING_CONFIG = create_custom_config('iqoptions', {
    'strategy_config': {
        'min_confidence': 0.55,
        'min_signal_interval': 10,
        'max_signals_per_hour': 30
    },
    'filters': {
        'enable_trend_filter': False,
        'enable_volatility_filter': False,
        'enable_session_filter': False
    }
})

CONSERVATIVE_TRADING_CONFIG = create_custom_config('iqoptions', {
    'strategy_config': {
        'min_confidence': 0.80,
        'min_signal_interval': 60,
        'max_signals_per_hour': 8
    },
    'filters': {
        'enable_trend_filter': True,
        'enable_volatility_filter': True,
        'enable_session_filter': True,
        'enable_confluence_filter': True
    }
})

BALANCED_TRADING_CONFIG = IQ_OPTIONS_OPTIMIZED_CONFIG  # Configuración balanceada por defecto

# Configuración por defecto (la más recomendada)
DEFAULT_CONFIG = IQ_OPTIONS_OPTIMIZED_CONFIG

# ================================
# EJEMPLO DE USO
# ================================

"""
# Uso básico:
from config.config import get_optimized_config, DEFAULT_CONFIG

# Usar configuración por defecto
config = DEFAULT_CONFIG

# O obtener configuración específica
config = get_optimized_config('iqoptions')

# Crear configuración personalizada
custom_config = create_custom_config('iqoptions', {
    'strategy_config': {
        'min_confidence': 0.70,
        'max_signals_per_hour': 15
    }
})

# Usar en el bot
bot = TradingBot(config)
await bot.start()
"""