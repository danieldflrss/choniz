# src/alerts/notification_system.py
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Any

from core.models.models import Signal, SignalType

# Primero necesitamos actualizar config.py para incluir configuraciones de notificaciones

# CONFIGURACIONES DE NOTIFICACIONES (agregar a config.py)
"""
    # CONFIGURACIONES DE NOTIFICACIONES
    NOTIFICATIONS_ENABLED = True  # Habilitar/deshabilitar notificaciones
    NOTIFICATION_TIMEOUT = 8  # Duración de notificación en segundos
    NOTIFICATION_COOLDOWN = 60  # Tiempo mínimo entre notificaciones del mismo asset (segundos)
"""

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("⚠️ Plyer no está disponible. Instala con: pip install plyer")

class NotificationSystem:
    """Sistema de notificaciones mejorado que recibe alertas del sistema de alertas"""
    
    def __init__(self):
        self.enabled = PLYER_AVAILABLE
        self.notification_history = []
        self.last_notification_time = {}
        
        # Configuración de notificaciones
        self.config = {
            'notification_timeout': 10,
            'notification_cooldown': 60,
            'max_notifications_per_minute': 10,
            'enable_system_notifications': True,
            'enable_signal_notifications': True,
            'enable_performance_notifications': True,
            'enable_error_notifications': True,
            'sound_enabled': True
        }
        
        # Contador de notificaciones por minuto
        self.notifications_this_minute = []
        
        if self.enabled:
            logging.info("🔔 Sistema de notificaciones inicializado correctamente")
        else:
            logging.warning("🔕 Sistema de notificaciones deshabilitado (plyer no disponible)")
    
    def process_alert(self, alert_data: Dict):
        """Método principal para procesar alertas del AlertSystem"""
        if not self.enabled:
            return
        
        alert_type = alert_data.get('type', 'SYSTEM')
        priority = alert_data.get('priority', 'MEDIUM')
        
        # Verificar si este tipo de notificación está habilitado
        if not self._is_notification_type_enabled(alert_type):
            return
        
        # Verificar límites de frecuencia
        if not self._check_rate_limits(alert_data):
            return
        
        # Procesar según el tipo de alerta
        if alert_type == 'SIGNAL':
            self._process_signal_alert(alert_data)
        elif alert_type == 'SYSTEM':
            self._process_system_alert(alert_data)
        elif alert_type == 'PERFORMANCE':
            self._process_performance_alert(alert_data)
        elif alert_type == 'ERROR':
            self._process_error_alert(alert_data)
        else:
            self._process_generic_alert(alert_data)
    
    def _is_notification_type_enabled(self, alert_type: str) -> bool:
        """Verifica si el tipo de notificación está habilitado"""
        type_mapping = {
            'SIGNAL': 'enable_signal_notifications',
            'SYSTEM': 'enable_system_notifications',
            'PERFORMANCE': 'enable_performance_notifications',
            'ERROR': 'enable_error_notifications'
        }
        
        config_key = type_mapping.get(alert_type, 'enable_system_notifications')
        return self.config.get(config_key, True)
    
    def _check_rate_limits(self, alert_data: Dict) -> bool:
        """Verifica límites de frecuencia de notificaciones"""
        current_time = datetime.now()
        
        # Limpiar notificaciones antiguas (más de 1 minuto)
        self.notifications_this_minute = [
            t for t in self.notifications_this_minute
            if (current_time - t).total_seconds() < 60
        ]
        
        # Verificar límite por minuto
        if len(self.notifications_this_minute) >= self.config['max_notifications_per_minute']:
            logging.warning("🚫 Límite de notificaciones por minuto alcanzado")
            return False
        
        # Verificar cooldown para señales del mismo símbolo
        if alert_data.get('type') == 'SIGNAL':
            metadata = alert_data.get('metadata', {})
            symbol = metadata.get('symbol', 'UNKNOWN')
            
            if symbol in self.last_notification_time:
                time_diff = (current_time - self.last_notification_time[symbol]).total_seconds()
                if time_diff < self.config['notification_cooldown']:
                    return False
            
            self.last_notification_time[symbol] = current_time
        
        # Registrar esta notificación
        self.notifications_this_minute.append(current_time)
        return True
    
    def _process_signal_alert(self, alert_data: Dict):
        """Procesa alertas de señales de trading"""
        try:
            signal_data = alert_data.get('signal_data', {})
            metadata = alert_data.get('metadata', {})
            priority = alert_data.get('priority', 'MEDIUM')
            
            # Crear Signal object si tenemos los datos
            if signal_data:
                # Reconstruir el objeto Signal
                signal = self._reconstruct_signal_from_data(signal_data)
                title, message, icon = self._prepare_signal_notification_content(signal, priority)
            else:
                # Usar datos de metadata
                title, message, icon = self._prepare_signal_notification_from_metadata(metadata, priority)
            
            # Enviar notificación
            self._send_notification(title, message, icon, alert_data)
            
        except Exception as e:
            logging.error(f"❌ Error procesando alerta de señal: {e}")
    
    def _process_system_alert(self, alert_data: Dict):
        """Procesa alertas del sistema"""
        try:
            message = alert_data.get('message', 'Alerta del sistema')
            priority = alert_data.get('priority', 'MEDIUM')
            
            # Emoji según prioridad
            priority_emoji = {
                'CRITICAL': '🚨',
                'HIGH': '⚠️',
                'MEDIUM': 'ℹ️',
                'LOW': '💡'
            }.get(priority, 'ℹ️')
            
            title = f"{priority_emoji} Sistema - {priority}"
            icon = self._get_system_icon()
            
            self._send_notification(title, message, icon, alert_data)
            
        except Exception as e:
            logging.error(f"❌ Error procesando alerta del sistema: {e}")
    
    def _process_performance_alert(self, alert_data: Dict):
        """Procesa alertas de rendimiento"""
        try:
            message = alert_data.get('message', 'Alerta de rendimiento')
            priority = alert_data.get('priority', 'MEDIUM')
            
            title = f"📊 Rendimiento - {priority}"
            icon = self._get_system_icon()
            
            self._send_notification(title, message, icon, alert_data)
            
        except Exception as e:
            logging.error(f"❌ Error procesando alerta de rendimiento: {e}")
    
    def _process_error_alert(self, alert_data: Dict):
        """Procesa alertas de error"""
        try:
            message = alert_data.get('message', 'Error del sistema')
            
            title = "❌ Error del Sistema"
            icon = self._get_system_icon()
            
            self._send_notification(title, message, icon, alert_data, timeout=10)  # Errores duran más
            
        except Exception as e:
            logging.error(f"❌ Error procesando alerta de error: {e}")
    
    def _process_generic_alert(self, alert_data: Dict):
        """Procesa alertas genéricas"""
        try:
            message = alert_data.get('message', 'Alerta genérica')
            priority = alert_data.get('priority', 'MEDIUM')
            
            title = f"📢 Alerta - {priority}"
            icon = self._get_system_icon()
            
            self._send_notification(title, message, icon, alert_data)
            
        except Exception as e:
            logging.error(f"❌ Error procesando alerta genérica: {e}")
    
    def _reconstruct_signal_from_data(self, signal_data: Dict) -> Signal:
        """Reconstruye objeto Signal desde datos del diccionario"""
        # Convertir string de vuelta a enum si es necesario
        if isinstance(signal_data.get('signal_type'), str):
            signal_data['signal_type'] = SignalType(signal_data['signal_type'])
        
        # Convertir timestamp string de vuelta a datetime si es necesario
        if isinstance(signal_data.get('timestamp'), str):
            signal_data['timestamp'] = datetime.fromisoformat(signal_data['timestamp'])
        
        return Signal(**signal_data)
    
    def _prepare_signal_notification_content(self, signal: Signal, priority: str) -> tuple[str, str, str]:
        """Prepara el contenido de la notificación basado en la señal y prioridad"""
        
        # Emojis según prioridad
        priority_emoji = {
            'CRITICAL': '🚨',
            'HIGH': '🔥',
            'MEDIUM': '⚡',
            'LOW': '💡'
        }.get(priority, '⚡')
        
        # Emoji según tipo de señal
        signal_emoji = "📈" if signal.signal_type == SignalType.CALL else "📉"
        
        # Título mejorado con prioridad
        title = f"{priority_emoji} {signal_emoji} {signal.signal_type.value} - {signal.symbol}"
        
        # Mensaje detallado según prioridad
        if priority in ['CRITICAL', 'HIGH']:
            message = (
                f"{signal_emoji} {signal.signal_type.value} en {signal.symbol}\n"
                f"💰 Precio: {signal.entry_price:.5f}\n"
                f"🎯 Confianza: {signal.confidence:.1%} ({priority})\n"
                f"⏰ Expira: {signal.expiry_time}m\n"
                f"📋 {signal.reason[:50]}\n"
                f"🕐 {signal.timestamp.strftime('%H:%M:%S')}"
            )
            
            # Agregar información adicional para alertas críticas/altas
            if signal.support_resistance:
                message += f"\n🎯 S/R: {signal.support_resistance:.5f}"
            if signal.stop_loss:
                message += f"\n🛑 SL: {signal.stop_loss:.5f}"
            if signal.take_profit:
                message += f"\n🎊 TP: {signal.take_profit:.5f}"
                
        else:
            # Mensaje más compacto para prioridades menores
            message = (
                f"{signal_emoji} {signal.signal_type.value} - {signal.symbol}\n"
                f"💰 {signal.entry_price:.5f} | 🎯 {signal.confidence:.1%}\n"
                f"📋 {signal.reason[:50]}{'...' if len(signal.reason) > 50 else ''}"
            )
        
        icon = self._get_system_icon()
        return title, message, icon
    
    def _prepare_signal_notification_from_metadata(self, metadata: Dict, priority: str) -> tuple[str, str, str]:
        """Prepara notificación desde metadata cuando no hay signal_data completo"""
        
        symbol = metadata.get('symbol', 'UNKNOWN')
        signal_type = metadata.get('signal_type', 'UNKNOWN')
        confidence = metadata.get('confidence', 0)
        entry_price = metadata.get('entry_price', 0)
        
        priority_emoji = {
            'CRITICAL': '🚨',
            'HIGH': '🔥',
            'MEDIUM': '⚡',
            'LOW': '💡'
        }.get(priority, '⚡')
        
        signal_emoji = "📈" if signal_type == 'CALL' else "📉"
        
        title = f"{priority_emoji} {signal_emoji} {signal_type} - {symbol}"
        
        message = (
            f"{signal_emoji} {signal_type} en {symbol}\n"
            f"💰 Precio: {entry_price:.5f}\n"
            f"🎯 Confianza: {confidence:.1%} ({priority})\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        
        icon = self._get_system_icon()
        return title, message, icon
    
    def _send_notification(self, title: str, message: str, icon: str, alert_data: Dict, timeout: Optional[int] = None):
        """Envía la notificación usando threading"""
        
        if timeout is None:
            timeout = self.config['notification_timeout']
        
        threading.Thread(
            target=self._send_notification_thread,
            args=(title[:256], message[:256], icon, alert_data, timeout),
            daemon=True
        ).start()
    
    def _send_notification_thread(self, title: str, message: str, icon: str, alert_data: Dict, timeout: int):
        """Envía la notificación en un hilo separado"""
        try:
            # Configurar parámetros de notificación
            notification_params = {
                'title': title,
                'message': message,
                'timeout': timeout,
                'app_name': 'Trading Alert System',
                'app_icon': icon if icon else None
            }
            
            # Filtrar parámetros None para evitar errores
            notification_params = {k: v for k, v in notification_params.items() if v is not None}
            
            # Enviar notificación
            if PLYER_AVAILABLE:
                notification.notify(**notification_params)
            else:
                # Fallback: mostrar en consola
                print(f"\n{'='*50}")
                print(f"📱 NOTIFICACIÓN: {title}")
                print(f"📄 {message}")
                print(f"{'='*50}\n")
            
            # Registrar en historial
            self.notification_history.append({
                'timestamp': datetime.now(),
                'title': title,
                'message': message,
                'alert_type': alert_data.get('type', 'UNKNOWN'),
                'priority': alert_data.get('priority', 'MEDIUM'),
                'alert_id': alert_data.get('id', 'unknown')
            })
            
            # Mantener solo las últimas 100 notificaciones
            if len(self.notification_history) > 100:
                self.notification_history = self.notification_history[-100:]
            
            logging.info(f"📱 Notificación enviada: {title}")
            
        except Exception as e:
            logging.error(f"❌ Error enviando notificación: {e}")
    
    def _get_system_icon(self) -> str:
        """Obtiene el icono apropiado según el sistema operativo"""
        import platform
        
        system = platform.system().lower()
        
        if system == "windows":
            return ""  # Plyer usará icono por defecto
        elif system == "darwin":  # macOS
            return ""  # Plyer usará icono por defecto
        elif system == "linux":
            return "dialog-information"  # Icono estándar de información
        else:
            return ""
    
    # MÉTODOS DE COMPATIBILIDAD CON LA IMPLEMENTACIÓN ANTERIOR
    def send_signal_notification(self, alert_data: Dict):
        """Método de compatibilidad - redirige a process_alert"""
        self.process_alert(alert_data)
    
    def send_system_notification(self, title: str, message: str, notification_type: str = "info"):
        """Envía notificaciones del sistema (método de compatibilidad)"""
        
        alert_data = {
            'id': f"sys_{int(datetime.now().timestamp() * 1000)}",
            'timestamp': datetime.now().isoformat(),
            'type': 'SYSTEM',
            'priority': 'MEDIUM',
            'message': message,
            'metadata': {'notification_type': notification_type}
        }
        
        self.process_alert(alert_data)
    
    # MÉTODOS DE CONFIGURACIÓN Y CONTROL
    def enable_notifications(self):
        """Habilita las notificaciones"""
        if PLYER_AVAILABLE:
            self.enabled = True
            print("🔔 Notificaciones habilitadas")
            logging.info("Notificaciones habilitadas")
        else:
            print("❌ Plyer no está disponible. Instala con: pip install plyer")
    
    def disable_notifications(self):
        """Deshabilita las notificaciones"""
        self.enabled = False
        print("🔕 Notificaciones deshabilitadas")
        logging.info("Notificaciones deshabilitadas")
    
    def configure_notifications(self, **config):
        """Configura parámetros del sistema de notificaciones"""
        
        valid_configs = {
            'notification_timeout',
            'notification_cooldown',
            'max_notifications_per_minute',
            'enable_system_notifications',
            'enable_signal_notifications',
            'enable_performance_notifications',
            'enable_error_notifications',
            'sound_enabled'
        }
        
        for key, value in config.items():
            if key in valid_configs:
                self.config[key] = value
                logging.info(f"🔧 Configuración de notificaciones actualizada: {key} = {value}")
            else:
                logging.warning(f"⚠️ Configuración desconocida: {key}")
    
    def get_notification_stats(self) -> dict:
        """Obtiene estadísticas de notificaciones enviadas"""
        if not self.notification_history:
            return {
                "total": 0, 
                "by_type": {}, 
                "by_priority": {},
                "last_notification": None,
                "notifications_this_minute": len(self.notifications_this_minute)
            }
        
        total = len(self.notification_history)
        by_type = {}
        by_priority = {}
        
        for notif in self.notification_history:
            # Contar por tipo
            alert_type = notif.get('alert_type', 'UNKNOWN')
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            
            # Contar por prioridad
            priority = notif.get('priority', 'MEDIUM')
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        return {
            "total": total,
            "by_type": by_type,
            "by_priority": by_priority,
            "last_notification": self.notification_history[-1]['timestamp'] if self.notification_history else None,
            "notifications_this_minute": len(self.notifications_this_minute),
            "rate_limit_active": len(self.notifications_this_minute) >= self.config['max_notifications_per_minute']
        }
    
    def clear_history(self):
        """Limpia el historial de notificaciones"""
        self.notification_history.clear()
        self.last_notification_time.clear()
        self.notifications_this_minute.clear()
        print("🗑️ Historial de notificaciones limpiado")
        logging.info("Historial de notificaciones limpiado")
    
    def get_recent_notifications(self, limit: int = 10) -> list:
        """Obtiene las notificaciones más recientes"""
        return self.notification_history[-limit:] if self.notification_history else []
    
    def test_notification(self):
        """Envía una notificación de prueba"""
        test_alert = {
            'id': f"test_{int(datetime.now().timestamp() * 1000)}",
            'timestamp': datetime.now().isoformat(),
            'type': 'SYSTEM',
            'priority': 'MEDIUM',
            'message': '🧪 PRUEBA DEL SISTEMA DE NOTIFICACIONES\n✅ Sistema funcionando correctamente',
            'metadata': {'test': True}
        }
        
        self.process_alert(test_alert)
        print("🧪 Notificación de prueba enviada")
    
    def __str__(self) -> str:
        """Representación string del sistema de notificaciones"""
        stats = self.get_notification_stats()
        return (f"NotificationSystem(habilitado={self.enabled}, "
                f"total_enviadas={stats['total']}, "
                f"por_minuto={stats['notifications_this_minute']})")
    
    def __repr__(self) -> str:
        return self.__str__()