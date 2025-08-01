import logging

from bot.trading_bot import TradingBot
import asyncio

from config.config import  DEFAULT_CONFIG

# ================================
# FUNCIÓN PRINCIPAL
# ================================

async def main():
    """Función principal del sistema"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Seleccionar configuración (cambiar según necesidad)
    config = DEFAULT_CONFIG  # Usar Binance por defecto
    
    # Crear y iniciar bot
    bot = TradingBot(config)
    
    try:
        await bot.start()
        
        # Mantener corriendo
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        bot.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        bot.stop()

if __name__ == "__main__":
    print("🔥 Sistema de Trading en Tiempo Real")
    print("=" * 50)
    print("Configuraciones disponibles:")
    print("1. Binance (Crypto) - Sin API key necesaria")
    print("2. Alpha Vantage (Forex) - Requiere API key")
    print("3. IEX Cloud (Stocks) - Requiere API token")
    print("=" * 50)
    
    asyncio.run(main())