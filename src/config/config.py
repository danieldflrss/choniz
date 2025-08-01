# ================================
# CONFIGURACIÓN PRINCIPAL
# ================================

# Configuración para diferentes fuentes de datos
BINANCE_CONFIG = {
    'data_source': 'binance',
    'symbol': 'BTCUSDT',  # Bitcoin/USDT
    'interval': '1m',
    'credentials': {}
}

FOREX_CONFIG = {
    'data_source': 'alphavantage',
    'symbol': 'EUR/USD',
    'interval': '1min',
    'credentials': {
        'api_key': '9Q5ZV1NEBFQQZ76L'
    }
}

STOCK_CONFIG = {
    'data_source': 'iex',
    'symbol': 'AAPL',  # Apple
    'interval': '1m',
    'credentials': {
        'api_token': 'TU_TOKEN_IEX_CLOUD'
    }
}

IQ_OPTIONS_CONFIG = {
    'data_source': 'iqoptions',
    'symbol': 'EURUSD-OTC',
    'interval': 60,
    'credentials': {
        'email': 'trader.iqoptions@gmail.com',
        'password': 'porunbeso99'
    }
}