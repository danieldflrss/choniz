from typing import Dict, List, Optional
from alerts.notification_system import NotificationSystem
from core.models.models import Signal, SignalType
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
import json
import asyncio
from enum import Enum


class AlertPriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    SIGNAL = "SIGNAL"
    SYSTEM = "SYSTEM"
    PERFORMANCE = "PERFORMANCE"
    ERROR = "ERROR"


class AlertSystem:
    """Sistema de alertas mejorado para señales y eventos del sistema"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
        self.max_history = 500  # Aumentado para mejor tracking

        # Configuración de alertas
        self.alert_config = {
            "min_confidence_for_high_priority": 0.85,
            "min_confidence_for_medium_priority": 0.70,
            "enable_duplicate_filter": True,
            "duplicate_timeout": 30,  # segundos
            "enable_sound_alerts": True,
            "enable_visual_alerts": True,
        }

        # Cache para evitar duplicados
        self.recent_alerts = {}

        # Estadísticas de alertas
        self.alert_stats = {
            "total_sent": 0,
            "by_priority": {p.value: 0 for p in AlertPriority},
            "by_type": {t.value: 0 for t in AlertType},
            "last_alert_time": None,
            "alerts_per_hour": 0,
        }

        self.notifocation_alert = NotificationSystem()

    async def send_signal_alert(self, signal: Signal):
        """Envía alerta de señal con procesamiento mejorado"""

        # Determinar prioridad basada en confianza y contexto
        priority = self._determine_signal_priority(signal)

        # Crear mensaje enriquecido
        alert_message = self._format_signal_alert(signal, priority)

        # Verificar duplicados
        if self._is_duplicate_alert(alert_message):
            return

        # Crear objeto de alerta completo
        alert_data = {
            "id": self._generate_alert_id(),
            "timestamp": signal.timestamp.isoformat(),
            "type": AlertType.SIGNAL.value,
            "priority": priority.value,
            "message": alert_message,
            "signal_data": asdict(signal),
            "metadata": {
                "symbol": signal.symbol,
                "signal_type": signal.signal_type.value,
                "confidence": signal.confidence,
                "entry_price": signal.entry_price,
                "expiry_time": signal.expiry_time,
                "market_context": self._get_market_context_for_alert(signal),
            },
        }

        # Enviar alerta
        await self._dispatch_alert(alert_data)

    async def send_system_alert(
        self,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        alert_type: AlertType = AlertType.SYSTEM,
        metadata: Dict = None,
    ):
        """Envía alerta del sistema"""

        alert_data = {
            "id": self._generate_alert_id(),
            "timestamp": datetime.now().isoformat(),
            "type": alert_type.value,
            "priority": priority.value,
            "message": message,
            "metadata": metadata or {},
        }

        await self._dispatch_alert(alert_data)

    async def send_performance_alert(self, metrics: Dict):
        """Envía alerta de rendimiento"""

        # Analizar métricas y determinar si requiere alerta
        alert_needed, priority, message = self._analyze_performance_metrics(metrics)

        if alert_needed:
            await self.send_system_alert(
                message, priority, AlertType.PERFORMANCE, {"metrics": metrics}
            )

    def _determine_signal_priority(self, signal: Signal) -> AlertPriority:
        """Determina la prioridad de una señal"""

        confidence = signal.confidence

        # Prioridad basada en confianza
        if confidence >= self.alert_config["min_confidence_for_high_priority"]:
            base_priority = AlertPriority.HIGH
        elif confidence >= self.alert_config["min_confidence_for_medium_priority"]:
            base_priority = AlertPriority.MEDIUM
        else:
            base_priority = AlertPriority.LOW

        # Ajustes adicionales
        priority_score = confidence

        # Bonus por proximidad a soporte/resistencia
        if signal.support_resistance:
            distance = (
                abs(signal.entry_price - signal.support_resistance) / signal.entry_price
            )
            if distance < 0.001:  # Muy cerca de nivel clave
                priority_score += 0.1

        # Bonus por múltiples razones (confluencia)
        reason_count = len(signal.reason.split(";"))
        if reason_count >= 3:
            priority_score += 0.05

        # Determinar prioridad final
        if priority_score >= 0.9:
            return AlertPriority.CRITICAL
        elif priority_score >= 0.85:
            return AlertPriority.HIGH
        elif priority_score >= 0.7:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW

    def _format_signal_alert(self, signal: Signal, priority: AlertPriority) -> str:
        """Formatea mensaje de alerta de señal mejorado"""

        # Emoji basado en tipo de señal y prioridad
        if signal.signal_type == SignalType.CALL:
            direction_emoji = (
                "🟢📈"
                if priority in [AlertPriority.HIGH, AlertPriority.CRITICAL]
                else "📈"
            )
        else:
            direction_emoji = (
                "🔴📉"
                if priority in [AlertPriority.HIGH, AlertPriority.CRITICAL]
                else "📉"
            )

        # Emoji de prioridad
        priority_emoji = {
            AlertPriority.CRITICAL: "🚨",
            AlertPriority.HIGH: "🔥",
            AlertPriority.MEDIUM: "⚡",
            AlertPriority.LOW: "💡",
        }.get(priority, "")

        # Formatear tiempo de expiración de manera más clara
        expiry_text = self._format_expiry_time(signal.expiry_time)

        # Mensaje principal
        main_message = (
            f"{priority_emoji} {direction_emoji} {signal.signal_type.value}\n"
            f"💰 Precio: {signal.entry_price:.5f}\n"
            f"🎯 Confianza: {signal.confidence:.1%}\n"
            f"🕐 Fecha: {signal.timestamp.strftime('%H:%M:%S')}\n"
            f"⏰ Expira: {expiry_text}\n"
        )

        # Información adicional según prioridad
        if priority in [AlertPriority.HIGH, AlertPriority.CRITICAL]:
            additional_info = []

            if signal.support_resistance:
                additional_info.append(f"🎯 S/R: {signal.support_resistance:.5f}")

            if signal.stop_loss:
                additional_info.append(f"🛑 SL: {signal.stop_loss:.5f}")

            if signal.take_profit:
                additional_info.append(f"🎊 TP: {signal.take_profit:.5f}")

            if additional_info:
                main_message += "\n".join(additional_info) + "\n"

        # Razón (siempre incluir)
        main_message += f"📋 Razón: {signal.reason}"

        # Contexto adicional para alertas críticas
        if priority == AlertPriority.CRITICAL:
            main_message += f"\n🌟 SEÑAL PREMIUM - Alta confluencia detectada"

        return main_message

    def _format_expiry_time(self, expiry_seconds: int) -> str:
        """Formatea el tiempo de expiración de manera clara"""
        if expiry_seconds <= 60:
            return f"{expiry_seconds}s"
        elif expiry_seconds <= 3600:
            minutes = expiry_seconds // 60
            seconds = expiry_seconds % 60
            return f"{minutes}m{seconds}s" if seconds > 0 else f"{minutes}m"
        else:
            hours = expiry_seconds // 3600
            minutes = (expiry_seconds % 3600) // 60
            return f"{hours}h{minutes}m" if minutes > 0 else f"{hours}h"

    def _get_market_context_for_alert(self, signal: Signal) -> Dict:
        """Obtiene contexto del mercado para la alerta"""
        current_time = signal.timestamp

        return {
            "time_of_day": current_time.strftime("%H:%M"),
            "day_of_week": current_time.strftime("%A"),
            "session": self._determine_trading_session(current_time),
            "signal_quality": "Premium" if signal.confidence > 0.85 else "Standard",
        }

    def _determine_trading_session(self, timestamp: datetime) -> str:
        """Determina la sesión de trading"""
        hour = timestamp.hour

        if 0 <= hour < 8:
            return "Asiática"
        elif 8 <= hour < 16:
            return "Europea"
        elif 16 <= hour < 22:
            return "Americana"
        else:
            return "Solapamiento"

    def _is_duplicate_alert(self, message: str) -> bool:
        """Verifica si es una alerta duplicada"""
        if not self.alert_config["enable_duplicate_filter"]:
            return False

        current_time = datetime.now()
        message_hash = hash(message)

        # Verificar si ya existe una alerta similar reciente
        if message_hash in self.recent_alerts:
            last_time = self.recent_alerts[message_hash]
            if (current_time - last_time).total_seconds() < self.alert_config[
                "duplicate_timeout"
            ]:
                return True

        # Actualizar cache
        self.recent_alerts[message_hash] = current_time

        # Limpiar cache antiguo
        cutoff_time = current_time - timedelta(
            seconds=self.alert_config["duplicate_timeout"] * 2
        )
        self.recent_alerts = {
            h: t for h, t in self.recent_alerts.items() if t > cutoff_time
        }

        return False

    def _generate_alert_id(self) -> str:
        """Genera ID único para la alerta"""
        return f"alert_{int(datetime.now().timestamp() * 1000)}"

    async def _dispatch_alert(self, alert_data: Dict):
        """Despacha la alerta a todos los canales configurados"""

        # Log de la alerta
        priority_symbol = {
            AlertPriority.CRITICAL.value: "🚨",
            AlertPriority.HIGH.value: "🔥",
            AlertPriority.MEDIUM.value: "⚡",
            AlertPriority.LOW.value: "💡",
        }.get(alert_data["priority"], "")

        self.logger.info(
            f"{priority_symbol} ALERTA [{alert_data['priority']}]: \n{alert_data['message']}"
        )

        # Guardar en historial
        self.alert_history.append(alert_data)

        # Mantener límite de historial
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history :]

        # Actualizar estadísticas
        self._update_alert_stats(alert_data)

        # Aquí puedes integrar con servicios externos:
        await self._send_to_channels(alert_data)

    async def _send_to_channels(self, alert_data: Dict):
        """Envía alerta a diferentes canales (Telegram, Discord, etc.)"""

        # Placeholder para integraciones externas
        # Ejemplo de implementación:

        # if self.telegram_bot:
        #     await self.telegram_bot.send_message(alert_data['message'])

        # if self.discord_webhook:
        #     await self.discord_webhook.send(alert_data['message'])

        # if self.email_service:
        #     await self.email_service.send_alert(alert_data)

        # Enviar a sistema de notificaciones mejorado
        if hasattr(self, "notifocation_alert") and self.notifocation_alert:
            self.notifocation_alert.process_alert(alert_data)

    def _update_alert_stats(self, alert_data: Dict):
        """Actualiza estadísticas de alertas"""
        self.alert_stats["total_sent"] += 1
        self.alert_stats["by_priority"][alert_data["priority"]] += 1
        self.alert_stats["by_type"][alert_data["type"]] += 1
        self.alert_stats["last_alert_time"] = alert_data["timestamp"]

        # Calcular alertas por hora (basado en las últimas 24 horas)
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)

        recent_alerts = [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"]) > one_hour_ago
        ]

        self.alert_stats["alerts_per_hour"] = len(recent_alerts)

    def _analyze_performance_metrics(
        self, metrics: Dict
    ) -> tuple[bool, AlertPriority, str]:
        """Analiza métricas de rendimiento y determina si necesita alerta"""

        alert_needed = False
        priority = AlertPriority.LOW
        message = ""

        # Verificar calidad de datos
        data_quality = metrics.get("data_quality_score", 1.0)
        if data_quality < 0.8:
            alert_needed = True
            priority = (
                AlertPriority.HIGH if data_quality < 0.6 else AlertPriority.MEDIUM
            )
            message = f"⚠️ Calidad de datos degradada: {data_quality:.1%}"

        # Verificar frecuencia de señales
        signals_per_hour = metrics.get("signals_per_hour", 0)
        if signals_per_hour > 20:  # Demasiadas señales
            alert_needed = True
            priority = AlertPriority.MEDIUM
            message = f"📊 Frecuencia alta de señales: {signals_per_hour}/hora - Posible sobreoptimización"
        elif (
            signals_per_hour < 1 and metrics.get("candles_processed", 0) > 60
        ):  # Muy pocas señales
            alert_needed = True
            priority = AlertPriority.MEDIUM
            message = f"📉 Frecuencia baja de señales: {signals_per_hour}/hora - Verificar filtros"

        # Verificar tiempo sin señales
        if self.alert_stats["last_alert_time"]:
            last_alert = datetime.fromisoformat(self.alert_stats["last_alert_time"])
            time_since_last = (datetime.now() - last_alert).total_seconds() / 3600

            if time_since_last > 4:  # Más de 4 horas sin señales
                alert_needed = True
                priority = AlertPriority.MEDIUM
                message = f"⏰ Sin señales por {time_since_last:.1f} horas - Verificar conexión y filtros"

        return alert_needed, priority, message

    def get_recent_alerts(
        self,
        limit: int = 20,
        priority_filter: Optional[AlertPriority] = None,
        type_filter: Optional[AlertType] = None,
    ) -> List[Dict]:
        """Obtiene alertas recientes con filtros opcionales"""

        filtered_alerts = self.alert_history

        # Aplicar filtros
        if priority_filter:
            filtered_alerts = [
                a for a in filtered_alerts if a["priority"] == priority_filter.value
            ]

        if type_filter:
            filtered_alerts = [
                a for a in filtered_alerts if a["type"] == type_filter.value
            ]

        # Ordenar por timestamp descendente y limitar
        sorted_alerts = sorted(
            filtered_alerts, key=lambda x: x["timestamp"], reverse=True
        )

        return sorted_alerts[:limit]

    def get_alert_statistics(self) -> Dict:
        """Obtiene estadísticas completas de alertas"""

        if not self.alert_history:
            return {"total_alerts": 0}

        # Estadísticas básicas
        stats = self.alert_stats.copy()

        # Estadísticas adicionales
        recent_24h = self._get_alerts_in_timeframe(hours=24)
        recent_1h = self._get_alerts_in_timeframe(hours=1)

        stats.update(
            {
                "alerts_last_24h": len(recent_24h),
                "alerts_last_hour": len(recent_1h),
                "avg_alerts_per_day": len(recent_24h),  # Aproximación
                "priority_distribution_24h": self._get_priority_distribution(
                    recent_24h
                ),
                "type_distribution_24h": self._get_type_distribution(recent_24h),
                "peak_hours": self._get_peak_alert_hours(),
                "alert_frequency_trend": self._calculate_frequency_trend(),
            }
        )

        return stats

    def _get_alerts_in_timeframe(self, hours: int) -> List[Dict]:
        """Obtiene alertas en un período de tiempo específico"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            alert
            for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]

    def _get_priority_distribution(self, alerts: List[Dict]) -> Dict[str, int]:
        """Obtiene distribución de prioridades"""
        distribution = {p.value: 0 for p in AlertPriority}

        for alert in alerts:
            priority = alert.get("priority", AlertPriority.LOW.value)
            distribution[priority] += 1

        return distribution

    def _get_type_distribution(self, alerts: List[Dict]) -> Dict[str, int]:
        """Obtiene distribución de tipos de alerta"""
        distribution = {t.value: 0 for t in AlertType}

        for alert in alerts:
            alert_type = alert.get("type", AlertType.SYSTEM.value)
            distribution[alert_type] += 1

        return distribution

    def _get_peak_alert_hours(self) -> List[int]:
        """Obtiene las horas pico de alertas"""
        hour_counts = {}

        for alert in self.alert_history[-200:]:  # Últimas 200 alertas
            try:
                alert_time = datetime.fromisoformat(alert["timestamp"])
                hour = alert_time.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except:
                continue

        # Obtener top 3 horas
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]

    def _calculate_frequency_trend(self) -> str:
        """Calcula tendencia en la frecuencia de alertas"""
        if len(self.alert_history) < 20:
            return "Insuficientes datos"

        # Comparar últimas 2 horas vs 2 horas anteriores
        now = datetime.now()
        last_2h = now - timedelta(hours=2)
        last_4h = now - timedelta(hours=4)

        recent_alerts = len(
            [
                a
                for a in self.alert_history
                if datetime.fromisoformat(a["timestamp"]) > last_2h
            ]
        )

        previous_alerts = len(
            [
                a
                for a in self.alert_history
                if last_4h < datetime.fromisoformat(a["timestamp"]) <= last_2h
            ]
        )

        if previous_alerts == 0:
            return "Creciente" if recent_alerts > 0 else "Estable"

        change_ratio = recent_alerts / previous_alerts

        if change_ratio > 1.5:
            return "Creciente"
        elif change_ratio < 0.5:
            return "Decreciente"
        else:
            return "Estable"

    def configure_alerts(self, **config):
        """Configura parámetros del sistema de alertas"""

        valid_configs = {
            "min_confidence_for_high_priority",
            "min_confidence_for_medium_priority",
            "enable_duplicate_filter",
            "duplicate_timeout",
            "enable_sound_alerts",
            "enable_visual_alerts",
        }

        for key, value in config.items():
            if key in valid_configs:
                self.alert_config[key] = value
                self.logger.info(f"🔧 Configuración actualizada: {key} = {value}")
            else:
                self.logger.warning(f"⚠️ Configuración desconocida: {key}")

    def create_custom_alert(
        self,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        metadata: Optional[Dict] = None,
    ):
        """Crea una alerta personalizada"""

        alert_data = {
            "id": self._generate_alert_id(),
            "timestamp": datetime.now().isoformat(),
            "type": AlertType.SYSTEM.value,
            "priority": priority.value,
            "message": f"📢 {message}",
            "metadata": metadata or {},
        }

        # Enviar de forma asíncrona
        asyncio.create_task(self._dispatch_alert(alert_data))

    def export_alert_history(
        self, format: str = "json", limit: Optional[int] = None
    ) -> str:
        """Exporta historial de alertas en formato especificado"""

        alerts_to_export = self.alert_history[-limit:] if limit else self.alert_history

        if format.lower() == "json":
            return json.dumps(alerts_to_export, indent=2, default=str)
        elif format.lower() == "csv":
            return self._export_to_csv(alerts_to_export)
        else:
            raise ValueError(f"Formato no soportado: {format}")

    def _export_to_csv(self, alerts: List[Dict]) -> str:
        """Exporta alertas a formato CSV"""
        if not alerts:
            return "No hay alertas para exportar"

        # Headers CSV
        csv_lines = [
            "timestamp,type,priority,message,signal_type,confidence,entry_price"
        ]

        for alert in alerts:
            # Extraer datos básicos
            timestamp = alert.get("timestamp", "")
            alert_type = alert.get("type", "")
            priority = alert.get("priority", "")
            message = alert.get("message", "").replace(",", ";").replace("\n", " ")

            # Extraer datos de señal si existen
            signal_data = alert.get("signal_data", {})
            signal_type = signal_data.get("signal_type", "")
            confidence = signal_data.get("confidence", "")
            entry_price = signal_data.get("entry_price", "")

            csv_line = f"{timestamp},{alert_type},{priority},{message},{signal_type},{confidence},{entry_price}"
            csv_lines.append(csv_line)

        return "\n".join(csv_lines)

    def get_high_priority_summary(self) -> Dict:
        """Obtiene resumen de alertas de alta prioridad"""

        high_priority_alerts = [
            alert
            for alert in self.alert_history
            if alert.get("priority")
            in [AlertPriority.HIGH.value, AlertPriority.CRITICAL.value]
        ]

        if not high_priority_alerts:
            return {"message": "No hay alertas de alta prioridad recientes"}

        # Análisis de las últimas 24 horas
        recent_high_priority = self._get_alerts_in_timeframe(24)
        recent_high_priority = [
            alert
            for alert in recent_high_priority
            if alert.get("priority")
            in [AlertPriority.HIGH.value, AlertPriority.CRITICAL.value]
        ]

        return {
            "total_high_priority": len(high_priority_alerts),
            "last_24h_high_priority": len(recent_high_priority),
            "latest_high_priority": (
                high_priority_alerts[-1] if high_priority_alerts else None
            ),
            "success_signals_high_priority": len(
                [
                    alert
                    for alert in recent_high_priority
                    if alert.get("type") == AlertType.SIGNAL.value
                    and alert.get("metadata", {}).get("signal_quality") == "Premium"
                ]
            ),
        }

    async def test_alert_system(self):
        """Prueba el sistema de alertas con una alerta de prueba"""

        test_alert = {
            "id": self._generate_alert_id(),
            "timestamp": datetime.now().isoformat(),
            "type": AlertType.SYSTEM.value,
            "priority": AlertPriority.MEDIUM.value,
            "message": "🧪 PRUEBA DEL SISTEMA DE ALERTAS\n✅ Todos los sistemas funcionando correctamente",
            "metadata": {"test": True, "system_status": "operational"},
        }

        await self._dispatch_alert(test_alert)
        self.logger.info("🧪 Prueba del sistema de alertas completada")

    def __str__(self) -> str:
        """Representación string del sistema de alertas"""
        return (
            f"AlertSystem(alertas_enviadas={self.alert_stats['total_sent']}, "
            f"última_alerta={self.alert_stats['last_alert_time']}, "
            f"alertas_por_hora={self.alert_stats['alerts_per_hour']})"
        )

    def __repr__(self) -> str:
        return self.__str__()
