from bybit_api import BybitAPI
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_chart_data():
    print("Тестируем получение данных для графика...")
    
    # Инициализируем API
    api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
    
    # Тестируем разные символы и интервалы
    test_cases = [
        ('BTCUSDT', '15'),
        ('ETHUSDT', '15'),
        ('BTCUSDT', '1'),
        ('BTCUSDT', '60'),
    ]
    
    for symbol, interval in test_cases:
        print(f"\nТестируем {symbol} с интервалом {interval} минут:")
        
        try:
            # Получаем данные
            klines = api.get_klines(symbol, interval, limit=50)
            
            if klines and len(klines) > 0:
                df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
                df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
                df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                
                print(f"  ✅ Получено записей: {len(df)}")
                print(f"  📅 Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
                print(f"  💰 Последняя цена: ${df['close'].iloc[-1]:.2f}")
                print(f"  📊 Диапазон цен: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                
                # Проверяем формат данных для графика
                sample_data = {
                    'time': int(df['timestamp'].iloc[0]) // 1000,
                    'open': float(df['open'].iloc[0]),
                    'high': float(df['high'].iloc[0]),
                    'low': float(df['low'].iloc[0]),
                    'close': float(df['close'].iloc[0])
                }
                print(f"  📋 Пример данных: {sample_data}")
                
            else:
                print(f"  ❌ Не удалось получить данные")
                
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_chart_data() 