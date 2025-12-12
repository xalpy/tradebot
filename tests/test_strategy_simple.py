#!/usr/bin/env python3
"""
Простой тест стратегии
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy import GhostTangentStrategy
import pandas as pd

def test_strategy():
    """Тестирует генерацию сигналов стратегией"""
    
    print("🧪 Тест стратегии...")
    
    try:
        # Создаем тестовые данные
        print("📊 Создаем тестовые данные...")
        
        # Простые тестовые данные
        test_data = {
            'timestamp': [1640995200000, 1640995260000, 1640995320000, 1640995380000, 1640995440000],
            'open': [50000.0, 50100.0, 50200.0, 50300.0, 50400.0],
            'high': [50100.0, 50200.0, 50300.0, 50400.0, 50500.0],
            'low': [49900.0, 50000.0, 50100.0, 50200.0, 50300.0],
            'close': [50100.0, 50200.0, 50300.0, 50400.0, 50500.0],
            'volume': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0],
            'turnover': [50000000.0, 55220000.0, 60360000.0, 65520000.0, 70700000.0]
        }
        
        df = pd.DataFrame(test_data)
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        print(f"✅ Создан DataFrame с {len(df)} записями")
        print(f"📅 Период: {df['time'].iloc[0]} - {df['time'].iloc[-1]}")
        
        # Тестируем стратегию
        print("🚀 Тестируем стратегию...")
        strategy = GhostTangentStrategy()
        
        signals = strategy.generate_signals(df)
        
        print(f"✅ Стратегия сгенерировала {len(signals)} сигналов")
        
        if signals:
            print("📊 Сигналы:")
            for i, signal in enumerate(signals):
                print(f"  {i+1}. {signal['time']} - {signal['type']} - ${signal['price']}")
        else:
            print("📊 Сигналов не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategy()

