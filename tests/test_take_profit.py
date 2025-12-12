from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_take_profit():
    print("🧪 Тестируем функциональность тейк-профита...")
    
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
    
    # Тестируем разные параметры тейк-профита
    test_cases = [
        {'take_profit_pct': None, 'description': 'Без тейк-профита'},
        {'take_profit_pct': 1.0, 'description': 'Тейк-профит 1%'},
        {'take_profit_pct': 2.0, 'description': 'Тейк-профит 2%'},
        {'take_profit_pct': 5.0, 'description': 'Тейк-профит 5%'},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n🔬 Тест {i}: {params['description']}")
        
        try:
            # Запускаем бэктест
            strategy = GhostTangentStrategy()
            backtester = Backtester(strategy)
            trades = backtester.run_with_params(
                df, 
                leverage=10,
                stop_loss_pct=2.0,
                take_profit_pct=params['take_profit_pct'],
                initial_balance=1000,
                trade_size_pct=3.0
            )
            
            if trades:
                # Анализируем результаты
                total_trades = len(trades)
                profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
                stop_loss_trades = sum(1 for trade in trades if trade['exit_reason'] == 'stop_loss')
                take_profit_trades = sum(1 for trade in trades if trade['exit_reason'] == 'take_profit')
                signal_trades = sum(1 for trade in trades if trade['exit_reason'] == 'signal')
                period_end_trades = sum(1 for trade in trades if trade['exit_reason'] == 'period_end')
                
                total_profit_pct = sum(trade['profit_pct'] for trade in trades)
                total_profit_usd = sum(trade['profit_usd'] for trade in trades)
                max_profit = max(trade['profit_pct'] for trade in trades)
                max_loss = min(trade['profit_pct'] for trade in trades)
                
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                
                print(f"   📈 Результаты:")
                print(f"      Всего сделок: {total_trades}")
                print(f"      Прибыльных: {profitable_trades} ({win_rate:.1f}%)")
                print(f"      По стоп-лоссу: {stop_loss_trades}")
                print(f"      По тейк-профиту: {take_profit_trades}")
                print(f"      По сигналу: {signal_trades}")
                print(f"      По концу периода: {period_end_trades}")
                print(f"      Общая прибыль: {total_profit_pct:.2f}% (${total_profit_usd:.2f})")
                print(f"      Макс. прибыль: {max_profit:.2f}%")
                print(f"      Макс. убыток: {max_loss:.2f}%")
                
                # Показываем примеры сделок по тейк-профиту
                if take_profit_trades > 0:
                    take_profit_examples = [t for t in trades if t['exit_reason'] == 'take_profit'][:3]
                    print(f"   💰 Примеры сделок по тейк-профиту:")
                    for j, trade in enumerate(take_profit_examples, 1):
                        print(f"      {j}. {trade['entry_type'].upper()} | Вход: ${trade['entry_price']:.2f} | "
                              f"Выход: ${trade['exit_price']:.2f} | Прибыль: {trade['profit_pct']:.2f}%")
                
            else:
                print(f"   ❌ Сделок не найдено")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def test_take_profit_combined_strategy():
    print("\n" + "="*60)
    print("🧪 Тестируем тейк-профит с комбинированной стратегией...")
    
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
    
    # Тестируем комбинированную стратегию с тейк-профитом
    test_cases = [
        {'take_profit_pct': None, 'description': 'Без тейк-профита'},
        {'take_profit_pct': 1.5, 'description': 'Тейк-профит 1.5%'},
        {'take_profit_pct': 3.0, 'description': 'Тейк-профит 3%'},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n🔬 Тест {i}: {params['description']}")
        
        try:
            # Запускаем бэктест с комбинированной стратегией
            from combined_strategy import CombinedStrategy
            strategy = CombinedStrategy()
            backtester = Backtester(strategy)
            trades = backtester.run_combined_strategy(
                df, 
                leverage=10,
                stop_loss_pct=2.0,
                take_profit_pct=params['take_profit_pct'],
                initial_balance=1000,
                trade_size_pct=3.0
            )
            
            if trades:
                # Анализируем результаты
                total_trades = len(trades)
                profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
                take_profit_trades = sum(1 for trade in trades if trade['exit_reason'] == 'take_profit')
                avg_confidence = sum(trade.get('confidence', 50) for trade in trades) / len(trades)
                
                total_profit_pct = sum(trade['profit_pct'] for trade in trades)
                total_profit_usd = sum(trade['profit_usd'] for trade in trades)
                
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                
                print(f"   📈 Результаты комбинированной стратегии:")
                print(f"      Всего сделок: {total_trades}")
                print(f"      Прибыльных: {profitable_trades} ({win_rate:.1f}%)")
                print(f"      По тейк-профиту: {take_profit_trades}")
                print(f"      Общая прибыль: {total_profit_pct:.2f}% (${total_profit_usd:.2f})")
                print(f"      Средняя уверенность: {avg_confidence:.1f}%")
                
            else:
                print(f"   ❌ Сделок не найдено")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    test_take_profit()
    test_take_profit_combined_strategy() 