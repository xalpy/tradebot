#!/usr/bin/env python3
"""
Простой тест для проверки исправления ошибки "unhashable type: 'dict'"
"""

def test_get_strategy_for_symbol():
    """Простой тест функции get_strategy_for_symbol"""
    print("🧪 Тестируем исправление 'unhashable type: dict'...")
    
    try:
        # Импортируем web_app
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_app", "web_app.py")
        web_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app)
        
        # Загружаем стратегии из файла
        web_app.load_symbol_strategies()
        print(f"📋 Загруженные стратегии: {web_app.symbol_strategies}")
        
        # Тестируем каждый символ
        for symbol in web_app.symbol_strategies.keys():
            print(f"\n🔍 Тестируем {symbol}...")
            try:
                strategy = web_app.get_strategy_for_symbol(symbol)
                print(f"✅ Успешно получена стратегия для {symbol}: {type(strategy).__name__}")
            except Exception as e:
                print(f"❌ Ошибка для {symbol}: {e}")
                return False
        
        print("\n🎉 Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_get_strategy_for_symbol()
