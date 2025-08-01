from typing import Dict, List
from core.models.models import Signal, SignalType
import logging
from dataclasses import asdict


class AlertSystem:
    """Sistema de alertas para señales"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
        
    async def send_alert(self, signal: Signal):
        """Envía alerta de señal"""
        alert_message = self._format_alert(signal)
        
        # Log de la alerta
        self.logger.info(f"📱 ALERTA: \n{alert_message}")
        
        # Guardar en historial
        self.alert_history.append({
            'timestamp': signal.timestamp.isoformat(),
            'message': alert_message,
            'signal': asdict(signal)
        })
        
        # Mantener solo las últimas 100 alertas
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        # Aquí puedes integrar con servicios de notificación:
        # - Telegram Bot
        # - Discord Webhook
        # - Email
        # - Push notifications
        
    def _format_alert(self, signal: Signal) -> str:
        """Formatea mensaje de alerta"""
        direction = "📈" if signal.signal_type == SignalType.CALL else "📉"
        
        return (
            f"{direction} {signal.signal_type.value}\n"
            f"Precio: {signal.entry_price:.5f}\n"
            f"Confianza: {signal.confidence:.1%}\n"
            f"Expira: {signal.expiry_time}s\n"
            f"Razón: {signal.reason}"
        )
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Obtiene alertas recientes"""
        return self.alert_history[-limit:]
