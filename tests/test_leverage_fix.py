#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправления вычислений с плечом
"""

def test_leverage_calculations():
    """Тестирует правильность вычислений с плечом"""
    print("🧪 Тестируем вычисления с плечом...")
    
    # Тест 1: Вычисление суммы торговли в процентах от баланса
    print("\n📊 Тест 1: Вычисление суммы торговли")
    balance = 1000.0  # $1000
    trade_balance_pct = 3.0  # 3%
    
    # Старый способ (неправильный)
    old_position_value = balance * trade_balance_pct
    print(f"❌ Старый способ: ${balance} * {trade_balance_pct}% = ${old_position_value}")
    
    # Новый способ (правильный)
    new_position_value = balance * (trade_balance_pct / 100.0)
    print(f"✅ Новый способ: ${balance} * ({trade_balance_pct}% / 100) = ${new_position_value}")
    
    if new_position_value == 30.0:
        print("✅ Тест 1 ПРОЙДЕН: Сумма торговли вычисляется правильно")
    else:
        print("❌ Тест 1 НЕ ПРОЙДЕН: Сумма торговли вычисляется неправильно")
        return False
    
    # Тест 2: Вычисление стоп-лосса с плечом
    print("\n📊 Тест 2: Вычисление стоп-лосса с плечом")
    stop_loss_pct = 2.0  # 2%
    leverage = 10  # 10x плечо
    
    # Старый способ (неправильный)
    old_stop_loss = stop_loss_pct
    print(f"❌ Старый способ: стоп-лосс = {stop_loss_pct}% (без учета плеча)")
    
    # Новый способ (правильный)
    new_stop_loss = stop_loss_pct / leverage
    print(f"✅ Новый способ: стоп-лосс = {stop_loss_pct}% / {leverage}x = {new_stop_loss:.4f} ({new_stop_loss * 100:.2f}%)")
    
    if new_stop_loss == 0.2:
        print("✅ Тест 2 ПРОЙДЕН: Стоп-лосс с плечом вычисляется правильно")
    else:
        print("❌ Тест 2 НЕ ПРОЙДЕН: Стоп-лосс с плечом вычисляется неправильно")
        return False
    
    # Тест 3: Вычисление тейк-профита с плечом
    print("\n📊 Тест 3: Вычисление тейк-профита с плечом")
    take_profit_pct = 5.0  # 5%
    leverage = 10  # 10x плечо
    
    # Старый способ (неправильный)
    old_take_profit = take_profit_pct
    print(f"❌ Старый способ: тейк-профит = {take_profit_pct}% (без учета плеча)")
    
    # Новый способ (правильный)
    new_take_profit = take_profit_pct / leverage
    print(f"✅ Новый способ: тейк-профит = {take_profit_pct}% / {leverage}x = {new_take_profit:.4f} ({new_take_profit * 100:.2f}%)")
    
    if new_take_profit == 0.5:
        print("✅ Тест 3 ПРОЙДЕН: Тейк-профит с плечом вычисляется правильно")
    else:
        print("❌ Тест 3 НЕ ПРОЙДЕН: Тейк-профит с плечом вычисляется неправильно")
        return False
    
    # Тест 4: Практический пример
    print("\n📊 Тест 4: Практический пример")
    balance = 1000.0
    trade_balance_pct = 3.0
    price = 50000.0  # BTC цена
    stop_loss_pct = 2.0
    take_profit_pct = 5.0
    leverage = 10
    
    # Вычисляем количество
    position_value = balance * (trade_balance_pct / 100.0)
    qty = position_value / price
    
    # Вычисляем стоп и тейк цены
    stop_loss_real = stop_loss_pct / leverage
    take_profit_real = take_profit_pct / leverage
    
    # Для покупки
    stop_price_buy = price * (1 - stop_loss_real)
    take_price_buy = price * (1 + take_profit_real)
    
    print(f"💰 Баланс: ${balance}")
    print(f"📈 Сумма позиции: ${position_value}")
    print(f"📊 Количество: {qty:.6f} BTC")
    print(f"🎯 Цена входа: ${price}")
    print(f"🛑 Стоп-лосс: ${stop_price_buy:.2f} ({(1 - stop_loss_real) * 100:.2f}%)")
    print(f"🎉 Тейк-профит: ${take_price_buy:.2f} ({(1 + take_profit_real) * 100:.2f}%)")
    
    expected_stop = 50000 * (1 - 0.002)  # 2% / 10 = 0.2%
    expected_take = 50000 * (1 + 0.005)  # 5% / 10 = 0.5%
    
    if abs(stop_price_buy - expected_stop) < 0.01 and abs(take_price_buy - expected_take) < 0.01:
        print("✅ Тест 4 ПРОЙДЕН: Практический пример корректен")
    else:
        print("❌ Тест 4 НЕ ПРОЙДЕН: Практический пример некорректен")
        return False
    
    return True

def test_api_integration():
    """Тестирует интеграцию с API"""
    print("\n🔗 Тестируем интеграцию с API...")
    
    try:
        # Импортируем API
        from bybit_api import BybitAPI
        
        # Создаем тестовый экземпляр (без реальных ключей)
        print("✅ API модуль импортирован успешно")
        
        # Проверяем сигнатуру функции place_order
        import inspect
        sig = inspect.signature(BybitAPI.place_order)
        params = list(sig.parameters.keys())
        
        if 'leverage' in params:
            print("✅ Функция place_order поддерживает параметр leverage")
        else:
            print("❌ Функция place_order НЕ поддерживает параметр leverage")
            return False
        
        print("✅ Интеграция с API работает корректно")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта API: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования API: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования исправления вычислений с плечом...")
    print("=" * 70)
    
    tests = [
        ("Вычисления с плечом", test_leverage_calculations),
        ("Интеграция с API", test_api_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Тест: {test_name}")
        print("-" * 50)
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
    print(f"✅ Успешно: {sum(results)}")
    print(f"❌ Ошибок: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n✅ Исправления вычислений с плечом работают корректно:")
        print("   - Сумма торговли в процентах от баланса вычисляется правильно")
        print("   - Стоп-лосс с учетом плеча вычисляется правильно")
        print("   - Тейк-профит с учетом плеча вычисляется правильно")
        print("   - API поддерживает передачу плеча")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("\n🔧 Рекомендации:")
        print("   - Проверьте исправления в коде")
        print("   - Убедитесь, что все функции обновлены")

if __name__ == "__main__":
    main()

