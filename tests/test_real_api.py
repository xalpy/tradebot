from bybit_api import BybitAPI
from config import REAL_API_KEY, REAL_API_SECRET

def test_real_api():
    print("Тестируем подключение с реальными API ключами...")
    
    try:
        # Инициализируем API с реальными ключами
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='real')
        
        print("✅ API инициализирован успешно")
        
        # Тестируем получение баланса
        try:
            balance = api.get_balance("USDT")
            print(f"✅ Баланс USDT: ${balance:.2f}")
        except Exception as e:
            print(f"❌ Ошибка получения баланса: {e}")
        
        # Тестируем получение всех балансов
        try:
            balances = api.get_all_balances()
            print(f"✅ Все балансы получены: {len(balances)} монет")
            for coin, amount in balances.items():
                print(f"   {coin}: {amount:.4f}")
        except Exception as e:
            print(f"❌ Ошибка получения всех балансов: {e}")
        
        # Тестируем получение данных графика
        try:
            klines = api.get_klines("BTCUSDT", "15", limit=10)
            print(f"✅ Данные графика получены: {len(klines)} записей")
            if klines:
                last_price = float(klines[-1][4])  # close price
                print(f"   Последняя цена BTC: ${last_price:.2f}")
        except Exception as e:
            print(f"❌ Ошибка получения данных графика: {e}")
        
        # Тестируем получение позиций
        try:
            positions = api.get_open_positions("BTCUSDT")
            print(f"✅ Позиции получены: {len(positions)} открытых позиций")
        except Exception as e:
            print(f"❌ Ошибка получения позиций: {e}")
        
        print("\n🎉 Все тесты завершены!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка инициализации API: {e}")

if __name__ == "__main__":
    test_real_api() 