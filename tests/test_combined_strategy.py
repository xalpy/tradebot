from bybit_api import BybitAPI
from combined_strategy import CombinedStrategy
from backtester import Backtester
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_combined_strategy():
    print("🧪 Тестируем комбинированную стратегию (GhostTangent + OTT)...")
    
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
    
    # Тестируем комбинированную стратегию
    print("\n🔬 Тестируем комбинированную стратегию:")
    
    try:
        # Создаем комбинированную стратегию
        combined_strategy = CombinedStrategy()
        
        # Получаем сигналы
        signals = combined_strategy.generate_signals(df)
        
        print(f"   📈 Найдено {len(signals)} совпадающих сигналов")
        
        if signals:
            # Показываем статистику стратегий
            stats = combined_strategy.get_strategy_stats()
            print(f"   📊 Статистика стратегий:")
            print(f"      Всего сигналов: {stats['total_signals']}")
            print(f"      Совпадающих: {stats['combined_signals']} ({stats['combined_percentage']}%)")
            print(f"      Только GhostTangent: {stats['ghost_only']}")
            print(f"      Только OTT: {stats['ott_only']}")
            print(f"      Противоречивых: {stats['conflicting']}")
            print(f"      Средняя уверенность: {stats['avg_confidence']}%")
            
            # Показываем последние сигналы
            print(f"   📋 Последние совпадающие сигналы:")
            for signal in signals[-5:]:
                confidence = signal.get('confidence', 50)
                print(f"      {signal['time']}: {signal['type'].upper()} "
                      f"(уверенность: {confidence}%, цена: ${signal['price']:.2f})")
            
            # Запускаем бэктест
            print(f"\n💰 Запускаем бэктест с комбинированной стратегией...")
            backtester = Backtester(combined_strategy)
            trades = backtester.run_combined_strategy(
                df, 
                leverage=10,
                stop_loss_pct=2.0,
                initial_balance=1000,
                trade_size_pct=3.0
            )
            
            if trades:
                # Анализируем результаты
                total_trades = len(trades)
                profitable_trades = sum(1 for trade in trades if trade['profit_pct'] > 0)
                total_profit_pct = sum(trade['profit_pct'] for trade in trades)
                total_profit_usd = sum(trade['profit_usd'] for trade in trades)
                max_profit = max(trade['profit_pct'] for trade in trades)
                max_loss = min(trade['profit_pct'] for trade in trades)
                avg_confidence = sum(trade.get('confidence', 50) for trade in trades) / len(trades)
                
                win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
                
                print(f"   📈 Результаты бэктеста:")
                print(f"      Всего сделок: {total_trades}")
                print(f"      Прибыльных: {profitable_trades} ({win_rate:.1f}%)")
                print(f"      Общая прибыль: {total_profit_pct:.2f}% (${total_profit_usd:.2f})")
                print(f"      Макс. прибыль: {max_profit:.2f}%")
                print(f"      Макс. убыток: {max_loss:.2f}%")
                print(f"      Средняя уверенность: {avg_confidence:.1f}%")
                
                # Показываем последние сделки
                print(f"   📋 Последние сделки:")
                for trade in trades[-3:]:
                    confidence = trade.get('confidence', 50)
                    exit_reason = trade.get('exit_reason', 'signal')
                    if exit_reason == 'stop_loss':
                        exit_reason = '🛑 Стоп-лосс'
                    elif exit_reason == 'signal':
                        exit_reason = '🔄 Сигнал'
                    else:
                        exit_reason = '⏰ Конец периода'
                    
                    print(f"      {trade['entry_type'].upper()} {trade['leverage']}x: "
                          f"{trade['profit_pct']:+.2f}% (${trade['profit_usd']:+.2f}) "
                          f"[уверенность: {confidence}%] - {exit_reason}")
                
            else:
                print("   ❌ Нет сделок в бэктесте")
        
        else:
            print("   ❌ Нет совпадающих сигналов")
        
        # Анализируем рыночные условия
        print(f"\n🌍 Анализ рыночных условий:")
        market_analysis = combined_strategy.analyze_market_conditions(df)
        print(f"   Тренд: {market_analysis['trend']}")
        print(f"   Волатильность: {market_analysis['volatility']}")
        print(f"   Рекомендация: {market_analysis['recommendation']}")
        print(f"   Текущий OTT: ${market_analysis['ott_current']:.2f} ({market_analysis['ott_color']})")
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_combined_strategy() 