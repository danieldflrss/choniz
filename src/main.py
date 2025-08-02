import logging

from bot.trading_bot import TradingBot
import asyncio

from config.config import DEFAULT_CONFIG

from config.config import get_optimized_config, DEFAULT_CONFIG, create_custom_config


# Agregar función para seleccionar configuración
def select_configuration():
    """Permite seleccionar configuración interactivamente"""
    print("\n🔧 Selecciona la configuración:")
    print("1. IQ Options (Recomendado)")
    print("2. Binance (Crypto)")
    print("3. Alpha Vantage (Forex)")
    print("4. IEX Cloud (Stocks)")
    print("5. Configuración personalizada")

    choice = input("\nOpción (1-5): ").strip()

    if choice == "1":
        return get_optimized_config("iqoptions")
    elif choice == "2":
        return get_optimized_config("binance")
    elif choice == "3":
        api_key = input("Ingresa tu API key de Alpha Vantage: ").strip()
        config = get_optimized_config("alphavantage")
        config["credentials"]["api_key"] = api_key
        return config
    elif choice == "4":
        api_token = input("Ingresa tu API token de IEX Cloud: ").strip()
        config = get_optimized_config("iex")
        config["credentials"]["api_token"] = api_token
        return config
    elif choice == "5":
        return create_custom_configuration()
    else:
        print("Opción inválida, usando configuración por defecto (IQ Options)")
        return DEFAULT_CONFIG


def create_custom_configuration():
    """Crea configuración personalizada"""
    print("\n🎯 Configuración personalizada:")

    min_confidence = float(input("Confianza mínima (0.6-0.9): ") or "0.65")
    max_signals_hour = int(input("Máximo señales por hora (5-30): ") or "15")

    base_config = get_optimized_config("iqoptions")

    overrides = {
        "strategy_config": {
            "min_confidence": min_confidence,
            "max_signals_per_hour": max_signals_hour,
        }
    }

    return create_custom_config("iqoptions", overrides)


# ================================
# FUNCIÓN PRINCIPAL
# ================================


async def main():
    """Función principal del sistema"""

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Seleccionar configuración
    try:
        config = select_configuration()
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
        return

    # Mostrar información de la configuración seleccionada
    print(f"\n✅ Configuración seleccionada: {config['data_source'].upper()}")
    print(f"📊 Símbolo: {config['symbol']}")
    print(f"🎯 Confianza mínima: {config['strategy_config']['min_confidence']:.1%}")
    print(f"⚡ Máx. señales/hora: {config['strategy_config']['max_signals_per_hour']}")

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
