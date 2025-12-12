from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_advanced_backtest():
    print("🧪 Тестируем продвинутый бэктест с плечом и стоп-лоссом...")
    
    # Инициализируем API
    api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
    
    # Получаем исторические данные
    print("📊 Получаем исторические данные...")
    klines = api.get_klines('BTCUSDT', '15', limit=500)
    
    if not klines:
        print("❌ Не удалось получить данные")
        return
    
    # Создаем DataFrame
    df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
    df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
    df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
    
    print(f"✅ Получено {len(df)} записей")
    print(f"📅 Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
    
    # Тестируем разные параметры
    test_cases = [
        {'leverage': 1, 'stop_loss_pct': 2.0, 'initial_balance': 1000, 'trade_size_pct': 3.0},
        {'leverage': 10, 'stop_loss_pct': 2.0, 'initial_balance': 1000, 'trade_size_pct': 3.0},
        {'leverage': 20, 'stop_loss_pct': 1.0, 'initial_balance': 1000, 'trade_size_pct': 5.0},
        {'leverage': 50, 'stop_loss_pct': 0.5, 'initial_balance': 1000, 'trade_size_pct': 2.0},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n🔬 Тест {i}: Плечо {params['leverage']}x, Стоп-лосс {params['stop_loss_pct']}%")
        print(f"   Баланс: ${params['initial_balance']}, Размер позиции: {params['trade_size_pct']}%")
        
        try:
            # Запускаем бэктест
            strategy = GhostTangentStrategy()
            backtester = Backtester(strategy)
            trades = backtester.run_with_params(
                df, 
                params['leverage'], 
                params['stop_loss_pct'], 
                params['initial_balance'], 
                params['trade_size_pct']
            )
            
            if trades:
                # Анализируем результаты
                total_trades = len(trades)
                profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
                stop_loss_trades = sum(1 for trade in trades if trade['exit_reason'] == 'stop_loss')
                total_profit_pct = sum(trade['profit_pct'] for trade in trades)
                total_profit_usd = sum(trade['profit_usd'] for trade in trades)
                max_profit = max(trade['profit_pct'] for trade in trades)
                max_loss = min(trade['profit_pct'] for trade in trades)
                
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                
                print(f"   📈 Результаты:")
                print(f"      Всего сделок: {total_trades}")
                print(f"      Прибыльных: {profitable_trades} ({win_rate:.1f}%)")
                print(f"      По стоп-лоссу: {stop_loss_trades}")
                print(f"      Общая прибыль: {total_profit_pct:.2f}% (${total_profit_usd:.2f})")
                print(f"      Макс. прибыль: {max_profit:.2f}%")
                print(f"      Макс. убыток: {max_loss:.2f}%")
                
                # Показываем последние 3 сделки
                print(f"   📋 Последние сделки:")
                for trade in trades[-3:]:
                    exit_reason = trade['exit_reason']
                    if exit_reason == 'stop_loss':
                        exit_reason = '🛑 Стоп-лосс'
                    elif exit_reason == 'signal':
                        exit_reason = '🔄 Сигнал'
                    else:
                        exit_reason = '⏰ Конец периода'
                    
                    print(f"      {trade['entry_type'].upper()} {trade['leverage']}x: "
                          f"{trade['profit_pct']:+.2f}% (${trade['profit_usd']:+.2f}) - {exit_reason}")
                
            else:
                print("   ❌ Нет сделок")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_advanced_backtest() 