from strategy import GhostTangentStrategy
from backtester import Backtester
import pandas as pd

def test_double_signals_logic():
    """
    Тестирует логику двойных сигналов на примере
    """
    print("Тестируем логику двойных сигналов...")
    
    # Создаем тестовые данные с сигналами
    test_data = [
        {'time': '2024-01-01 10:00:00', 'type': 'buy', 'price': 100},
        {'time': '2024-01-01 11:00:00', 'type': 'sell', 'price': 105},  # Противоположный сигнал
        {'time': '2024-01-01 12:00:00', 'type': 'buy', 'price': 103},   # Снова противоположный
        {'time': '2024-01-01 13:00:00', 'type': 'sell', 'price': 108},  # И снова
        {'time': '2024-01-01 14:00:00', 'type': 'buy', 'price': 106},   # И еще раз
    ]
    
    print("Тестовые сигналы:")
    for i, signal in enumerate(test_data, 1):
        print(f"{i}. {signal['time']} - {signal['type'].upper()} @ ${signal['price']}")
    
    print("\nЛогика двойных сигналов:")
    current_position = None
    current_entry = None
    trades = []
    
    for signal in test_data:
        if current_position is None:
            # Нет позиции - открываем новую
            current_position = signal['type']
            current_entry = signal
            print(f"  Открываем позицию: {signal['type'].upper()} @ ${signal['price']}")
        else:
            # Есть позиция - проверяем на противоположный сигнал
            if ((current_position == 'buy' and signal['type'] == 'sell') or 
                (current_position == 'sell' and signal['type'] == 'buy')):
                
                # Закрываем текущую позицию и открываем новую
                exit_price = signal['price']
                entry_price = current_entry['price']
                
                if current_position == 'buy':
                    profit_pct = (exit_price - entry_price) / entry_price * 100
                    profit_usd = exit_price - entry_price
                else:  # sell
                    profit_pct = (entry_price - exit_price) / entry_price * 100
                    profit_usd = entry_price - exit_price
                
                print(f"  Закрываем {current_position.upper()} @ ${entry_price}")
                print(f"  Открываем {signal['type'].upper()} @ ${exit_price}")
                print(f"  Прибыль: {profit_pct:.2f}% (${profit_usd:.2f})")
                
                # Создаем запись о сделке
                trade = {
                    'entry_time': current_entry['time'],
                    'entry_type': current_position,
                    'entry_price': entry_price,
                    'exit_time': signal['time'],
                    'exit_type': signal['type'],
                    'exit_price': exit_price,
                    'profit_pct': round(profit_pct, 2),
                    'profit_usd': round(profit_usd, 2),
                    'status': 'profitable' if profit_pct > 0 else 'loss'
                }
                trades.append(trade)
                
                # Открываем новую позицию
                current_position = signal['type']
                current_entry = signal
            else:
                print(f"  Сигнал того же типа ({signal['type']}), позиция остается открытой")
    
    print(f"\nРезультат:")
    print(f"Всего сделок: {len(trades)}")
    if trades:
        profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
        total_profit_pct = sum(trade['profit_pct'] for trade in trades)
        win_rate = (profitable_trades / len(trades)) * 100
        
        print(f"Прибыльных сделок: {profitable_trades}")
        print(f"Винрейт: {win_rate:.2f}%")
        print(f"Общая прибыль: {total_profit_pct:.2f}%")
        
        print(f"\nДетали сделок:")
        for i, trade in enumerate(trades, 1):
            status = "✅" if trade['profit_pct'] > 0 else "❌"
            print(f"{i}. {trade['entry_type'].upper()} ${trade['entry_price']} → {trade['exit_type'].upper()} ${trade['exit_price']} | "
                  f"{trade['profit_pct']}% (${trade['profit_usd']}) {status}")

def test_strategy_signals():
    """
    Тестирует генерацию сигналов стратегией
    """
    print("\n" + "="*50)
    print("Тестируем генерацию сигналов стратегией...")
    
    # Создаем тестовые данные
    dates = pd.date_range('2024-01-01', periods=100, freq='15min')
    test_df = pd.DataFrame({
        'timestamp': [int(d.timestamp() * 1000) for d in dates],
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100 + i * 0.1 + 2 for i in range(100)],
        'low': [100 + i * 0.1 - 1 for i in range(100)],
        'close': [100 + i * 0.1 + 0.5 for i in range(100)],
        'volume': [1000 + i * 10 for i in range(100)],
        'turnover': [100000 + i * 1000 for i in range(100)]
    })
    test_df['time'] = pd.to_datetime(test_df['timestamp'], unit='ms')
    
    # Генерируем сигналы
    strategy = GhostTangentStrategy(pivot_forward=5, max_zig=3)  # Уменьшаем параметры для теста
    signals = strategy.generate_signals(test_df)
    
    print(f"Сгенерировано сигналов: {len(signals)}")
    if signals:
        print("Первые 5 сигналов:")
        for i, signal in enumerate(signals[:5], 1):
            print(f"{i}. {signal['time']} - {signal['type'].upper()} @ ${signal['price']:.2f}")
    
    # Тестируем бэктест
    backtester = Backtester(strategy)
    trades = backtester.run(test_df)
    
    print(f"\nРезультат бэктеста:")
    print(f"Всего сделок: {len(trades)}")
    if trades:
        profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
        total_profit_pct = sum(trade['profit_pct'] for trade in trades)
        win_rate = (profitable_trades / len(trades)) * 100
        
        print(f"Прибыльных сделок: {profitable_trades}")
        print(f"Винрейт: {win_rate:.2f}%")
        print(f"Общая прибыль: {total_profit_pct:.2f}%")

if __name__ == "__main__":
    test_double_signals_logic()
    test_strategy_signals() 