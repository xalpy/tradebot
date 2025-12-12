#!/usr/bin/env python3
"""
Скрипт для очистки и исправления стратегий
"""

import json
import re

def clean_strategies_file():
    """Очищает файл стратегий от неправильных данных"""
    print("🧹 Очищаем файл стратегий...")
    
    try:
        # Читаем текущий файл
        with open('symbol_strategies.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📋 Исходные данные: {data}")
        
        # Функция для проверки торговой пары
        def is_valid_trading_pair(symbol):
            return bool(re.match(r'^[A-Z]{2,10}USDT$|^[A-Z]{2,10}BTC$', symbol))
        
        # Очищаем стратегии
        if 'strategies' in data:
            original_strategies = data['strategies']
            cleaned_strategies = {}
            
            for symbol, strategy in original_strategies.items():
                if is_valid_trading_pair(symbol):
                    cleaned_strategies[symbol] = strategy
                    print(f"✅ Сохраняем стратегию для {symbol}")
                else:
                    print(f"🗑️ Удаляем невалидную стратегию: {symbol}")
            
            data['strategies'] = cleaned_strategies
        else:
            # Если нет вложенной структуры, проверяем корневые ключи
            cleaned_strategies = {}
            for symbol, strategy in data.items():
                if is_valid_trading_pair(symbol):
                    cleaned_strategies[symbol] = strategy
                    print(f"✅ Сохраняем стратегию для {symbol}")
                else:
                    print(f"🗑️ Удаляем невалидную стратегию: {symbol}")
            
            data = {"strategies": cleaned_strategies}
        
        # Сохраняем очищенный файл
        with open('symbol_strategies.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Файл очищен. Осталось стратегий: {len(data['strategies'])}")
        print(f"📋 Очищенные стратегии: {data['strategies']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        return False

def test_strategies_loading():
    """Тестирует загрузку стратегий"""
    print("\n🧪 Тестируем загрузку стратегий...")
    
    try:
        # Импортируем функцию загрузки
        import sys
        sys.path.append('.')
        
        # Создаем временный модуль для тестирования
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_app", "web_app.py")
        web_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app)
        
        # Тестируем загрузку
        web_app.load_symbol_strategies()
        
        print(f"✅ Загрузка стратегий работает")
        print(f"📋 Загруженные стратегии: {web_app.symbol_strategies}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    print("🚀 Запуск исправления стратегий...")
    
    # Очищаем файл
    if clean_strategies_file():
        print("✅ Очистка завершена успешно")
    else:
        print("❌ Ошибка очистки")
        return
    
    # Тестируем загрузку
    if test_strategies_loading():
        print("✅ Тестирование завершено успешно")
    else:
        print("❌ Ошибка тестирования")

if __name__ == "__main__":
    main()
