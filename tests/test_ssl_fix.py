#!/usr/bin/env python3
"""
Тест для проверки исправления SSL ошибки с Bybit testnet API
"""

from bybit_api import BybitAPI
from config import TEST_API_KEY, TEST_API_SECRET

def test_ssl_fix():
    """Тестирует исправление SSL ошибки"""
    print("🔧 Тестируем исправление SSL ошибки...")
    
    try:
        # Создаем API клиент в testnet режиме
        print("📡 Создаем API клиент для testnet...")
        api = BybitAPI(
            api_key=TEST_API_KEY, 
            api_secret=TEST_API_SECRET, 
            trade_mode='test'
        )
        print("✅ API клиент создан успешно")
        
        # Тестируем получение данных
        print("📊 Тестируем получение данных...")
        klines = api.get_klines('BTCUSDT', '15', limit=10)
        
        if klines:
            print(f"✅ Получено {len(klines)} записей")
            print(f"📈 Последняя цена: ${float(klines[-1][4])}")
            return True
        else:
            print("❌ Не удалось получить данные")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_ssl_fix()
    if success:
        print("🎉 SSL исправление работает!")
    else:
        print("💥 SSL исправление не работает")

