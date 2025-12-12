from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_new_backtest():
    print("Тестируем новую логику бэктеста с двойными сигналами...")
    
    # Инициализируем API
    api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
    
    # Получаем исторические данные
    symbol = 'BTCUSDT'
    interval = '15'
    
    print(f"Получаем данные для {symbol}, интервал {interval}...")
    
    klines = api.get_klines(symbol, interval, limit=1000)
    df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
    df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
    df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
    
    print(f"Получено {len(df)} записей")
    print(f"Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
    
    # Запускаем бэктест
    strategy = GhostTangentStrategy()
    backtester = Backtester(strategy)
    
    print("\nЗапускаем бэктест...")
    trades = backtester.run(df)
    
    print(f"\nРезультаты бэктеста:")
    print(f"Всего сделок: {len(trades)}")
    
    if trades:
        profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
        total_profit_pct = sum(trade['profit_pct'] for trade in trades)
        total_profit_usd = sum(trade['profit_usd'] for trade in trades)
        max_profit = max(trade['profit_pct'] for trade in trades)
        max_loss = min(trade['profit_pct'] for trade in trades)
        avg_duration = sum(trade['duration_hours'] for trade in trades) / len(trades)
        
        win_rate = (profitable_trades / len(trades)) * 100
        
        print(f"Прибыльных сделок: {profitable_trades}")
        print(f"Винрейт: {win_rate:.2f}%")
        print(f"Общая прибыль: {total_profit_pct:.2f}%")
        print(f"Общая прибыль USD: ${total_profit_usd:.2f}")
        print(f"Максимальная прибыль: {max_profit:.2f}%")
        print(f"Максимальный убыток: {max_loss:.2f}%")
        print(f"Средняя длительность: {avg_duration:.1f} часов")
        
        print(f"\nПоследние 5 сделок (от новых к старым):")
        # Показываем сделки от новых к старым
        for i, trade in enumerate(reversed(trades[-5:]), 1):
            status = "✅" if trade['profit_pct'] > 0 else "❌"
            print(f"{i}. {trade['entry_type'].upper()} | Вход: ${trade['entry_price']:.2f} | Выход: ${trade['exit_price']:.2f} | "
                  f"Прибыль: {trade['profit_pct']:.2f}% (${trade['profit_usd']:.2f}) | "
                  f"Длительность: {trade['duration_hours']}ч {status}")
        
        if len(trades) > 5:
            print(f"... и еще {len(trades) - 5} сделок")
    else:
        print("Сделок не найдено")

if __name__ == "__main__":
    test_new_backtest() 