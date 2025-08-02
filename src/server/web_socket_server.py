import logging
from dataclasses import asdict
import json
from datetime import datetime
from typing import Dict, Optional

from core.models.models import Candle, Signal


class WebSocketServer:
    """Servidor WebSocket para interface web"""

    def __init__(
        self, host: str = "localhost", port: int = 8765, config: Optional[Dict] = None
    ):
        if config:
            websocket_config = config.get("system", {}).get("websocket_config", {})
            self.host = websocket_config.get("host", host)
            self.port = websocket_config.get("port", port)
            self.enable_real_time_broadcast = websocket_config.get(
                "enable_real_time_broadcast", True
            )
        else:
            self.host = host
            self.port = port
            self.enable_real_time_broadcast = True

        self.clients = set()
        self.logger = logging.getLogger(__name__)

    async def register_client(self, websocket, path):
        """Registra nuevo cliente"""
        self.clients.add(websocket)
        self.logger.info(f"Cliente conectado: {websocket.remote_address}")

        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            self.logger.info(f"Cliente desconectado: {websocket.remote_address}")

    async def broadcast_signal(self, signal: Signal):
        """Transmite señal a todos los clientes conectados"""
        if not self.enable_real_time_broadcast:
            return

        if self.clients:
            message = json.dumps(
                {
                    "type": "signal",
                    "data": asdict(signal),
                    "timestamp": signal.timestamp.isoformat(),
                },
                default=str,
            )

            # Enviar a todos los clientes
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(message)
                except Exception as e:
                    self.logger.error(f"Error enviando a cliente: {e}")
                    disconnected.add(client)

            # Limpiar clientes desconectados
            self.clients -= disconnected

    async def broadcast_candle(self, candle: Candle):
        """Transmite nueva vela a clientes"""
        if self.clients:
            message = json.dumps(
                {
                    "type": "candle",
                    "data": asdict(candle),
                    "timestamp": datetime.fromtimestamp(candle.timestamp).isoformat(),
                }
            )

            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(message)
                except Exception:
                    disconnected.add(client)

            self.clients -= disconnected

    async def start_server(self):
        """Inicia servidor WebSocket"""
        import websockets

        self.logger.info(f"Iniciando WebSocket server en {self.host}:{self.port}")
        await websockets.serve(self.register_client, self.host, self.port)
