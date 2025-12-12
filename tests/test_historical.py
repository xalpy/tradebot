from bybit_api import BybitAPI
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_historical_data():
    print("Тестируем получение исторических данных...")
    
    # Инициализируем API с реальными ключами
    api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
    
    # Тестируем получение данных для разных интервалов
    intervals = ['1', '5', '15', '30', '60']
    symbol = 'BTCUSDT'
    
    for interval in intervals:
        print(f"\nТестируем интервал {interval} минут:")
        
        try:
            # Получаем данные
            klines = api.get_klines(symbol, interval, limit=1000)
            
            if klines:
                df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
                df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
                df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                
                print(f"  Получено записей: {len(df)}")
                print(f"  Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
                print(f"  Последняя цена: ${df['close'].iloc[-1]:.2f}")
                
                # Проверяем уникальность временных меток
                unique_timestamps = df['timestamp'].nunique()
                print(f"  Уникальных временных меток: {unique_timestamps}")
                
                if unique_timestamps != len(df):
                    print(f"  ВНИМАНИЕ: Есть дубликаты временных меток!")
                
            else:
                print("  Не удалось получить данные")
                
        except Exception as e:
            print(f"  Ошибка: {e}")

if __name__ == "__main__":
    test_historical_data() 