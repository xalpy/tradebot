#!/usr/bin/env python3
"""
Прямой тест бектеста без веб-интерфейса
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
import pandas as pd

def test_backtest_direct():
    """Тестирует бектест напрямую"""
    
    print("🧪 Прямой тест бектеста...")
    
    try:
        # Инициализируем API
        print("🔧 Инициализируем API...")
        api = BybitAPI()
        
        # Получаем данные
        print("📊 Получаем исторические данные...")
        symbol = "BTCUSDT"
        interval = "15"
        days_back = 7
        
        klines = api.get_klines(symbol, interval, limit=1000)
        if not klines:
            print("❌ Не удалось получить данные")
            return
        
        print(f"✅ Получено {len(klines)} записей")
        
        # Создаем DataFrame
        df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
        df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
        df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        
        print(f"📅 Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
        
        # Запускаем бектест
        print("🚀 Запускаем бектест...")
        strategy = GhostTangentStrategy()
        backtester = Backtester(strategy)
        
        leverage = 10
        stop_loss_pct = 2.0
        take_profit_pct = None
        initial_balance = 1000.0
        trade_size_pct = 3.0
        
        signals = backtester.run_with_params(
            df, leverage, stop_loss_pct, take_profit_pct, 
            initial_balance, trade_size_pct
        )
        
        print(f"✅ Бектест завершен!")
        print(f"📊 Количество сделок: {len(signals)}")
        
        if signals:
            print(f"📊 Первая сделка: {signals[0]}")
            
            # Статистика
            profitable_trades = sum(1 for trade in signals if trade['profit_pct'] > 0)
            total_profit_pct = sum(trade['profit_pct'] for trade in signals)
            win_rate = (profitable_trades / len(signals) * 100) if signals else 0
            
            print(f"📈 Статистика:")
            print(f"  - Всего сделок: {len(signals)}")
            print(f"  - Прибыльных: {profitable_trades}")
            print(f"  - Винрейт: {win_rate:.2f}%")
            print(f"  - Общая прибыль: {total_profit_pct:.2f}%")
        else:
            print("📊 Сделок не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backtest_direct()

