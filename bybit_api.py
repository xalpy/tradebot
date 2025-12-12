from pybit.unified_trading import HTTP
from config import TEST_API_KEY, TEST_API_SECRET, REAL_API_KEY, REAL_API_SECRET
import math
import urllib3
import requests
import time
import json

class BybitAPI:
    def __init__(self, api_key, api_secret, trade_mode='test'):
        self.trade_mode = trade_mode
        self.time_offset = 0  # Смещение времени между локальным и серверным временем
        
        if trade_mode == 'real':
            self.session = HTTP(
                api_key=api_key,
                api_secret=api_secret,
                testnet=False
            )
        else:
            # Для testnet отключаем SSL verification
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Создаем кастомную сессию requests с отключенной SSL проверкой
            custom_session = requests.Session()
            custom_session.verify = False
            
            # Создаем HTTP сессию для testnet
            self.session = HTTP(
                api_key=api_key,
                api_secret=api_secret,
                testnet=True
            )
            
            # Заменяем сессию в HTTP менеджере pybit
            if hasattr(self.session, '_http_manager') and hasattr(self.session._http_manager, 'client'):
                self.session._http_manager.client = custom_session
        
        # Синхронизируем время с сервером при инициализации
        self.sync_server_time()
        
        # Настраиваем кастомную временную метку для HTTP менеджера
        self._setup_custom_timestamp()

    def get_server_time(self):
        """Получает время сервера Bybit в миллисекундах"""
        try:
            if self.trade_mode == 'real':
                url = "https://api.bybit.com/v5/market/time"
            else:
                url = "https://api-testnet.bybit.com/v5/market/time"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("retCode") == 0:
                    server_time = int(data["result"]["timeSecond"]) * 1000  # Конвертируем в миллисекунды
                    return server_time
            return None
        except Exception as e:
            print(f"⚠️ Ошибка получения времени сервера: {e}")
            return None

    def sync_server_time(self):
        """Синхронизирует локальное время с сервером Bybit"""
        try:
            print("🕐 Синхронизация времени с сервером Bybit...")
            
            # Получаем время сервера
            server_time = self.get_server_time()
            if server_time is None:
                print("⚠️ Не удалось получить время сервера, используем локальное время")
                return
            
            # Получаем локальное время в миллисекундах
            local_time = int(time.time() * 1000)
            
            # Вычисляем смещение
            self.time_offset = server_time - local_time
            
            print(f"✅ Время синхронизировано. Смещение: {self.time_offset} мс")
            print(f"   Локальное время: {local_time}")
            print(f"   Серверное время: {server_time}")
            
        except Exception as e:
            print(f"⚠️ Ошибка синхронизации времени: {e}")
            self.time_offset = 0

    def get_synchronized_timestamp(self):
        """Возвращает синхронизированную временную метку в миллисекундах"""
        return int(time.time() * 1000) + self.time_offset

    def _setup_custom_timestamp(self):
        """Настраивает кастомную временную метку для HTTP менеджера pybit"""
        try:
            if hasattr(self.session, '_http_manager'):
                # Сохраняем оригинальный метод генерации временной метки
                original_timestamp = getattr(self.session._http_manager, '_generate_timestamp', None)
                
                # Создаем кастомную функцию генерации временной метки
                def custom_timestamp():
                    return str(self.get_synchronized_timestamp())
                
                # Заменяем метод генерации временной метки
                self.session._http_manager._generate_timestamp = custom_timestamp
                
                print("✅ Настроена кастомная генерация временных меток")
                
        except Exception as e:
            print(f"⚠️ Ошибка настройки кастомной временной метки: {e}")

    def resync_time(self):
        """Повторно синхронизирует время с сервером"""
        print("🔄 Повторная синхронизация времени...")
        self.sync_server_time()
        self._setup_custom_timestamp()

    def get_symbol_info(self, symbol):
        print(f"📊 Запрос информации о {symbol} к Bybit API...")
        res = self.session.get_instruments_info(
            category="linear",
            symbol=symbol
        )
        print(f"📊 Ответ от Bybit для {symbol}: {res.get('retCode')} - {res.get('retMsg', '')}")
        if res.get("retCode") == 0 and res["result"]["list"]:
            print(f"✅ Информация о {symbol} получена успешно")
            return res["result"]["list"][0]
        else:
            print(f"❌ Ошибка получения информации о тикере {symbol}: {res}")
            return None

    def get_last_price(self, symbol):
        """Возвращает актуальную последнюю цену символа из тикера."""
        try:
            res = self.session.get_tickers(category="linear", symbol=symbol)
            if res.get("retCode") == 0 and res.get("result", {}).get("list"):
                return float(res["result"]["list"][0]["lastPrice"])
        except Exception as e:
            print(f"Ошибка получения тикера для {symbol}: {e}")
        # Фолбэк: последняя свеча, если тикер недоступен
        klines = self.get_klines(symbol, interval="1", limit=1)
        return float(klines[-1][4])
    
    def get_all_trading_pairs(self):
        """Получает все доступные торговые пары"""
        try:
            print("📊 Запрос всех торговых пар к Bybit API...")
            res = self.session.get_instruments_info(category="linear")
            print(f"📊 Ответ от Bybit: {res.get('retCode')} - {res.get('retMsg', '')}")
            if res.get("retCode") == 0:
                pairs = []
                for item in res["result"]["list"]:
                    # Фильтруем только активные пары с USDT
                    if (item.get("status") == "Trading" and 
                        item.get("quoteCoin") == "USDT" and
                        float(item.get("volume24h", 0)) > 1000):  # Минимальный объем
                        pairs.append({
                            "symbol": item["symbol"],
                            "baseCoin": item["baseCoin"],
                            "quoteCoin": item["quoteCoin"],
                            "volume24h": float(item.get("volume24h", 0)),
                            "price": float(item.get("lastPrice", 0))
                        })
                
                # Сортируем по объему торгов
                pairs.sort(key=lambda x: x["volume24h"], reverse=True)
                return pairs
            else:
                print(f"Ошибка получения торговых пар: {res}")
                return []
        except Exception as e:
            print(f"Ошибка получения торговых пар: {e}")
            return []
    
    def get_popular_pairs(self):
        """Получает популярные торговые пары"""
        popular_symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", 
            "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
            "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
            "BCHUSDT", "FILUSDT", "NEARUSDT", "APTUSDT", "OPUSDT"
        ]
        
        try:
            print("📊 Запрос популярных торговых пар к Bybit API...")
            res = self.session.get_instruments_info(category="linear")
            print(f"📊 Ответ от Bybit: {res.get('retCode')} - {res.get('retMsg', '')}")
            if res.get("retCode") == 0:
                pairs = []
                for item in res["result"]["list"]:
                    if (item["symbol"] in popular_symbols and 
                        item.get("status") == "Trading"):
                        pairs.append({
                            "symbol": item["symbol"],
                            "baseCoin": item["baseCoin"],
                            "quoteCoin": item["quoteCoin"],
                            "volume24h": float(item.get("volume24h", 0)),
                            "price": float(item.get("lastPrice", 0))
                        })
                
                # Сортируем по порядку в списке популярных
                pairs.sort(key=lambda x: popular_symbols.index(x["symbol"]))
                return pairs
            else:
                print(f"Ошибка получения популярных пар: {res}")
                return []
        except Exception as e:
            print(f"Ошибка получения популярных пар: {e}")
            return []

    def round_to_step(self, value, step):
        # Округляет value до ближайшего шага step
        return math.floor(float(value) / float(step)) * float(step)

    def get_klines(self, symbol, interval, limit=200):
        res = self.session.get_kline(
            category="linear",
            symbol=symbol,
            interval=str(interval),
            limit=limit
        )
        if res.get("retCode") == 0:
            return res["result"]["list"]
        else:
            raise Exception(f"Bybit API error: {res}")

    def set_leverage(self, symbol, buy_leverage=1, sell_leverage=1):
        res = self.session.set_leverage(
            category="linear",
            symbol=symbol,
            buyLeverage=str(buy_leverage),
            sellLeverage=str(sell_leverage)
        )
        if res.get("retCode") == 0:
            print(f"Leverage set: buy={buy_leverage}, sell={sell_leverage}")
            return True
        else:
            print(f"Ошибка установки плеча: {res}")
            return False

    def get_trade_history(self, symbol=None, limit=50):
        """Получает историю сделок из Bybit API.
        
        Args:
            symbol: Торговая пара (например, 'BTCUSDT') или None для всех
            limit: Количество сделок для получения (максимум 50)
        
        Returns:
            list: Список сделок с информацией о прибыли/убытке
        """
        try:
            print(f"📊 Запрос истории сделок для {symbol or 'всех символов'}...")
            
            # Получаем историю сделок
            res = self.session.get_executions(
                category="linear",
                symbol=symbol,
                limit=limit
            )
            
            if res.get("retCode") != 0:
                print(f"❌ Ошибка получения истории сделок: {res}")
                return []
            
            executions = res.get("result", {}).get("list", []) or []
            print(f"✅ Получено {len(executions)} сделок")
            
            # Обрабатываем сделки и группируем по символам
            processed_trades = {}
            
            for execution in executions:
                symbol_name = execution.get("symbol", "")
                side = execution.get("side", "")
                size = float(execution.get("execQty", 0) or 0)
                price = float(execution.get("execPrice", 0) or 0)
                exec_time = execution.get("execTime", "")
                exec_fee = float(execution.get("execFee", 0) or 0)
                
                if symbol_name not in processed_trades:
                    processed_trades[symbol_name] = {
                        'symbol': symbol_name,
                        'total_buy_qty': 0,
                        'total_sell_qty': 0,
                        'total_buy_value': 0,
                        'total_sell_value': 0,
                        'total_fees': 0,
                        'trades': []
                    }
                
                trade_info = {
                    'side': side,
                    'size': size,
                    'price': price,
                    'value': size * price,
                    'time': exec_time,
                    'fee': exec_fee
                }
                
                processed_trades[symbol_name]['trades'].append(trade_info)
                processed_trades[symbol_name]['total_fees'] += exec_fee
                
                if side == 'Buy':
                    processed_trades[symbol_name]['total_buy_qty'] += size
                    processed_trades[symbol_name]['total_buy_value'] += size * price
                else:
                    processed_trades[symbol_name]['total_sell_qty'] += size
                    processed_trades[symbol_name]['total_sell_value'] += size * price
            
            # Рассчитываем PnL для каждого символа
            for symbol_name, data in processed_trades.items():
                # Простой расчет PnL: разность между продажами и покупками
                if data['total_buy_qty'] > 0 and data['total_sell_qty'] > 0:
                    avg_buy_price = data['total_buy_value'] / data['total_buy_qty']
                    avg_sell_price = data['total_sell_value'] / data['total_sell_qty']
                    
                    # PnL = (средняя цена продажи - средняя цена покупки) * количество
                    min_qty = min(data['total_buy_qty'], data['total_sell_qty'])
                    pnl = (avg_sell_price - avg_buy_price) * min_qty - data['total_fees']
                    
                    data['pnl'] = pnl
                    data['pnl_percentage'] = (pnl / data['total_buy_value']) * 100 if data['total_buy_value'] > 0 else 0
                else:
                    data['pnl'] = 0
                    data['pnl_percentage'] = 0
            
            return list(processed_trades.values())
            
        except Exception as e:
            print(f"❌ Ошибка получения истории сделок: {e}")
            return []

    def get_open_positions(self, symbol=None):
        # Получаем позиции по USDT линейным контрактам
        try:
            if symbol:
                # Запрос по конкретному символу
                res = self.session.get_positions(
                    category="linear",
                    symbol=symbol
                )
                
                if res.get("retCode") != 0:
                    print(f"Ошибка получения позиций для {symbol}: {res}")
                    return []

                positions = res.get("result", {}).get("list", []) or []
                # Фильтруем только активные позиции с ненулевым размером
                open_positions = []
                for pos in positions:
                    try:
                        size = float(pos.get("size", 0) or 0)
                        if size > 0:
                            open_positions.append(pos)
                    except Exception:
                        continue
                return open_positions
            else:
                # Запрос по всем популярным символам
                popular_symbols = [
                    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", 
                    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
                    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
                    "BCHUSDT", "FILUSDT", "NEARUSDT", "APTUSDT", "OPUSDT"
                ]
                
                all_positions = []
                print(f"🔍 Запрос позиций по {len(popular_symbols)} популярным символам...")
                
                for symbol in popular_symbols:
                    try:
                        res = self.session.get_positions(
                            category="linear",
                            symbol=symbol
                        )
                        
                        if res.get("retCode") == 0:
                            positions = res.get("result", {}).get("list", []) or []
                            # Фильтруем только активные позиции с ненулевым размером
                            for pos in positions:
                                try:
                                    size = float(pos.get("size", 0) or 0)
                                    if size > 0:
                                        all_positions.append(pos)
                                except Exception:
                                    continue
                        else:
                            print(f"⚠️ Ошибка получения позиций для {symbol}: {res.get('retMsg', 'Unknown error')}")
                            
                    except Exception as e:
                        print(f"⚠️ Исключение при запросе позиций для {symbol}: {e}")
                        continue
                
                print(f"✅ Найдено {len(all_positions)} активных позиций")
                return all_positions
                
        except Exception as e:
            print(f"❌ Общая ошибка запроса позиций: {e}")
            return []

    def get_balance(self, coin="USDT"):
        print(f"💰 Запрос баланса {coin} к Bybit API...")
        res = self.session.get_wallet_balance(
            accountType="UNIFIED",
            coin=coin
        )
        print(f"💰 Ответ от Bybit: {res.get('retCode')} - {res.get('retMsg', '')}")
        if res.get("retCode") == 0:
            try:
                return float(res["result"]["list"][0]["totalEquity"])
            except Exception:
                print(f"Ошибка парсинга баланса: {res}")
                return 0.0
        else:
            print(f"Ошибка получения баланса: {res}")
            return 0.0

    def get_all_balances(self):
        res = self.session.get_wallet_balance(accountType="UNIFIED")
        balances = {}
        if res.get("retCode") == 0:
            for acc in res["result"]["list"]:
                for coin in acc["coin"]:
                    total = float(coin.get("equity", 0))
                    if total > 0:
                        balances[coin["coin"]] = total
            return balances
        else:
            print(f"Ошибка получения балансов: {res}")
            return {}

    def place_order(self, symbol, side, qty, price=None, stop_loss=None, take_profit=None, order_type="Market", reduce_only=False, leverage=1):
        # Нормализуем единицы: значения > 1 считаем процентами и делим на 100
        # Но только если они действительно больше 1 (чтобы не сломать уже нормализованные значения)
        if stop_loss is not None and stop_loss > 1 and stop_loss <= 100:
            stop_loss = float(stop_loss) / 100.0
        if take_profit is not None and take_profit > 1 and take_profit <= 100:
            take_profit = float(take_profit) / 100.0
        
        # Учитываем плечо: реальные уровни = уровни / leverage
        if stop_loss is not None and stop_loss > 0 and leverage > 1:
            stop_loss = stop_loss / leverage
            print(f"🔧 Учитываем плечо {leverage}x: стоп-лосс {stop_loss * leverage:.2f}% -> {stop_loss:.4f}")
        
        if take_profit is not None and take_profit > 0 and leverage > 1:
            take_profit = take_profit / leverage
            print(f"🔧 Учитываем плечо {leverage}x: тейк-профит {take_profit * leverage:.2f}% -> {take_profit:.4f}")

        # Получаем шаги цены и количества
        info = self.get_symbol_info(symbol)
        tick_size = float(info["priceFilter"]["tickSize"]) if info else 0.01
        lot_size = float(info["lotSizeFilter"]["qtyStep"]) if info else 0.001
        min_qty = float(info["lotSizeFilter"].get("minOrderQty", lot_size)) if info else lot_size
        
        # Дополнительно округляем qty до 2 знаков после запятой для всех символов
        qty = round(qty, 2)
        
        # Округляем qty по шагу лота
        qty = max(self.round_to_step(qty, lot_size), min_qty)
        
        # Финальное округление до 2 знаков для гарантии корректного формата
        qty = round(qty, 2)
        print(f"🔧 {symbol}: qty после округления: {qty} (исходный: {qty}, lot_size: {lot_size})")
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "reduceOnly": reduce_only,
        }
        if price is not None and order_type == "Limit":
            price = self.round_to_step(price, tick_size)
            params["price"] = str(price)
        if stop_loss is not None and stop_loss > 0:
            # Опорная цена входа: лимитная цена (если есть) vs актуальная последняя цена
            live_price = self.get_last_price(symbol)
            candidate = price if (price is not None and order_type == "Limit") else None
            if side == "Buy":
                entry_ref = max(candidate or 0, live_price)
            else:
                entry_ref = min(candidate or float('inf'), live_price)
            entry_ref = self.round_to_step(entry_ref, tick_size)

            if side == "Buy":
                stop_price = entry_ref * (1 - stop_loss)
                # Гарантируем, что стоп хотя бы на 5 тиков ниже опорной цены
                min_stop = entry_ref - 5 * tick_size
                if stop_price >= min_stop:
                    stop_price = min_stop
            else:
                stop_price = entry_ref * (1 + stop_loss)
                # Гарантируем, что стоп хотя бы на 5 тиков выше опорной цены
                min_stop = entry_ref + 5 * tick_size
                if stop_price <= min_stop:
                    stop_price = min_stop

            stop_price = self.round_to_step(stop_price, tick_size)
            print(f"[DEBUG] live_price={live_price}, entry_ref={entry_ref}, stop_price={stop_price}, stop_loss={stop_loss}, side={side}, tick_size={tick_size}, lot_size={lot_size}")
            params["stopLoss"] = str(stop_price)
        
        if take_profit is not None and take_profit > 0:
            # Опорная цена входа: лимитная цена (если есть) vs актуальная последняя цена
            live_price = self.get_last_price(symbol)
            candidate = price if (price is not None and order_type == "Limit") else None
            if side == "Buy":
                entry_ref = max(candidate or 0, live_price)
            else:
                entry_ref = min(candidate or float('inf'), live_price)
            entry_ref = self.round_to_step(entry_ref, tick_size)

            if side == "Buy":
                take_profit_price = entry_ref * (1 + take_profit)
                # Гарантируем, что TP как минимум на 5 тиков выше опорной
                min_tp = entry_ref + 5 * tick_size
                if take_profit_price <= min_tp:
                    take_profit_price = min_tp
            else:
                take_profit_price = entry_ref * (1 - take_profit)
                # Гарантируем, что TP как минимум на 5 тиков ниже опорной
                min_tp = entry_ref - 5 * tick_size
                if take_profit_price >= min_tp:
                    take_profit_price = min_tp

            take_profit_price = self.round_to_step(take_profit_price, tick_size)
            print(f"[DEBUG] live_price={live_price}, entry_ref={entry_ref}, take_profit_price={take_profit_price}, take_profit={take_profit}, side={side}, tick_size={tick_size}, lot_size={lot_size}")
            params["takeProfit"] = str(take_profit_price)
        # Логируем параметры ордера перед отправкой
        order_value = float(qty) * (float(price) if price else float(self.get_last_price(symbol)))
        print(f"📊 Отправляем ордер: {symbol} {side} {qty} @ {price or 'MARKET'} (стоимость: ${order_value:.2f})")
        print(f"📊 Параметры: stop_loss={params.get('stopLoss', 'None')}, take_profit={params.get('takeProfit', 'None')}")
        
        res = self.session.place_order(**params)
        if res.get("retCode") == 0:
            print(f"✅ Ордер размещён: {side}, qty={qty}, stop_loss={stop_loss}, take_profit={take_profit}")
            return res["result"]
        else:
            print(f"❌ Ошибка размещения ордера: {res}")
            return None 