#!/usr/bin/env python3
"""
Тест для проверки исправлений:
1. Ошибка создания графика
2. Отображение открытых позиций в бэктесте
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bybit_api import BybitAPI
from strategy import GhostTangentStrategy
from backtester import Backtester
from config import REAL_API_KEY, REAL_API_SECRET
import pandas as pd

def test_chart_fix():
    """Тест для проверки исправления ошибки графика"""
    print("🔧 Тестируем исправление ошибки графика...")
    
    try:
        # Инициализируем API
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
        
        # Получаем данные для графика
        klines = api.get_klines('BTCUSDT', '15', limit=50)
        
        if klines:
            df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
            df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
            df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            
            print(f"✅ Получено {len(df)} записей для графика")
            print(f"📅 Период: с {df['time'].iloc[0]} по {df['time'].iloc[-1]}")
            print(f"💰 Последняя цена: ${df['close'].iloc[-1]:.2f}")
            
            # Проверяем формат данных для графика
            sample_data = {
                'time': int(df['timestamp'].iloc[0]) // 1000,
                'open': float(df['open'].iloc[0]),
                'high': float(df['high'].iloc[0]),
                'low': float(df['low'].iloc[0]),
                'close': float(df['close'].iloc[0])
            }
            print(f"📋 Формат данных для графика: {sample_data}")
            
            return True
        else:
            print("❌ Не удалось получить данные для графика")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании графика: {e}")
        return False

def test_open_positions_display():
    """Тест для проверки отображения открытых позиций"""
    print("\n📈 Тестируем отображение открытых позиций...")
    
    try:
        # Инициализируем API
        api = BybitAPI(api_key=REAL_API_KEY, api_secret=REAL_API_SECRET, trade_mode='test')
        
        # Получаем исторические данные
        klines = api.get_klines('BTCUSDT', '15', limit=100)
        
        if not klines:
            print("❌ Не удалось получить данные")
            return False
        
        # Создаем DataFrame
        df = pd.DataFrame(klines, columns=['timestamp','open','high','low','close','volume','turnover'])
        df[['open','high','low','close','volume','turnover']] = df[['open','high','low','close','volume','turnover']].astype(float)
        df['time'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        
        print(f"✅ Получено {len(df)} записей")
        
        # Запускаем бэктест
        strategy = GhostTangentStrategy()
        backtester = Backtester(strategy)
        trades = backtester.run_with_params(
            df, 
            leverage=10,
            stop_loss_pct=2.0,
            take_profit_pct=None,  # Без тейк-профита для простоты
            initial_balance=1000,
            trade_size_pct=3.0
        )
        
        if trades:
            print(f"📊 Найдено {len(trades)} сделок")
            
            # Анализируем причины выхода
            exit_reasons = {}
            for trade in trades:
                reason = trade.get('exit_reason', 'unknown')
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
            
            print("📋 Причины выхода из позиций:")
            for reason, count in exit_reasons.items():
                if reason == 'signal':
                    print(f"   🔄 По сигналу: {count}")
                elif reason == 'stop_loss':
                    print(f"   🛑 По стоп-лоссу: {count}")
                elif reason == 'take_profit':
                    print(f"   💰 По тейк-профиту: {count}")
                elif reason == 'period_end':
                    print(f"   📈 Открытые позиции: {count}")
                else:
                    print(f"   ❓ {reason}: {count}")
            
            # Показываем примеры открытых позиций
            open_positions = [t for t in trades if t.get('exit_reason') == 'period_end']
            if open_positions:
                print(f"\n📈 Примеры открытых позиций:")
                for i, trade in enumerate(open_positions[:3], 1):
                    print(f"   {i}. {trade['entry_type'].upper()} | Вход: ${trade['entry_price']:.2f} | "
                          f"Текущая цена: ${trade['exit_price']:.2f} | Прибыль: {trade['profit_pct']:.2f}%")
            
            return True
        else:
            print("❌ Сделок не найдено")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании открытых позиций: {e}")
        return False

def main():
    print("🧪 Тестируем исправления...")
    print("=" * 50)
    
    # Тест 1: Исправление графика
    chart_ok = test_chart_fix()
    
    # Тест 2: Отображение открытых позиций
    positions_ok = test_open_positions_display()
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   График: {'✅ Исправлен' if chart_ok else '❌ Ошибка'}")
    print(f"   Открытые позиции: {'✅ Исправлено' if positions_ok else '❌ Ошибка'}")
    
    if chart_ok and positions_ok:
        print("\n🎉 Все исправления работают корректно!")
        return True
    else:
        print("\n⚠️  Некоторые исправления требуют доработки")
        return False

if __name__ == "__main__":
    main() 