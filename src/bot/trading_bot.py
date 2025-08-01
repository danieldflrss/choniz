from typing import Dict
from alerts.alert_system import AlertSystem
from core.system.real_time_market_system import RealTimeMarketSystem
from server.web_socket_server import WebSocketServer
import logging


class TradingBot:
    """Bot de trading completo"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.alert_system = AlertSystem()
        self.ws_server = WebSocketServer()
        self.logger = logging.getLogger(__name__)
        
        # Configurar sistema de mercado
        data_source = config.get('data_source', 'binance')
        credentials = config.get('credentials', {})
        
        self.market_system = RealTimeMarketSystem(data_source, **credentials)
        
        # Configurar callbacks
        self.market_system.add_signal_callback(self.alert_system.send_signal_alert)
        self.market_system.add_signal_callback(self.ws_server.broadcast_signal)
    
    async def start(self):
        """Inicia el bot completo"""
        try:
            self.logger.info("🚀 Iniciando Trading Bot...")
            
            # Iniciar servidor WebSocket
            await self.ws_server.start_server()
            
            # Iniciar análisis de mercado
            symbol = self.config.get('symbol', 'BTCUSDT')
            interval = self.config.get('interval', '1m')
            
            await self.market_system.start_real_time_analysis(symbol, interval)
            
        except Exception as e:
            self.logger.error(f"Error iniciando bot: {e}")
            raise
    
    def stop(self):
        """Detiene el bot"""
        self.market_system.stop()
        self.logger.info("🛑 Trading Bot detenido")