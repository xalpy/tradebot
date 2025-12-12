from strategy import GhostTangentStrategy
from ott_strategy import OTTStrategy
import pandas as pd

class CombinedStrategy:
    """
    Комбинированная стратегия, использующая GhostTangent и OTT
    Сделки совершаются только при совпадении сигналов обоих индикаторов
    """
    
    def __init__(self, 
                 ghost_pivot_period=5, 
                 ghost_min_strength=0.5,
                 ott_length=2, 
                 ott_percent=1.4, 
                 ott_ma_type="VAR"):
        
        self.ghost_strategy = GhostTangentStrategy(
            pivot_period=ghost_pivot_period,
            max_zig=ghost_min_strength
        )
        
        self.ott_strategy = OTTStrategy(
            length=ott_length,
            percent=ott_percent,
            ma_type=ott_ma_type
        )
        
        self.last_ghost_signal = None
        self.last_ott_signal = None
        self.signal_history = []
    
    def generate_signals(self, df):
        """
        Генерирует сигналы на основе совпадения двух стратегий
        """
        # Получаем сигналы от обеих стратегий
        ghost_signals = self.ghost_strategy.generate_signals(df)
        ott_signals = self.ott_strategy.generate_signals(df)
        
        # Создаем словари для быстрого поиска сигналов по времени
        # Преобразуем время в строку для хеширования
        ghost_signals_dict = {str(signal['time']): signal for signal in ghost_signals}
        ott_signals_dict = {str(signal['time']): signal for signal in ott_signals}
        
        # Находим совпадающие сигналы
        combined_signals = []
        
        # Проверяем все временные точки
        all_times = set(ghost_signals_dict.keys()) | set(ott_signals_dict.keys())
        
        for time in sorted(all_times):
            ghost_signal = ghost_signals_dict.get(str(time))
            ott_signal = ott_signals_dict.get(str(time))
            
            # Если есть сигнал от обеих стратегий
            if ghost_signal and ott_signal:
                # Проверяем совпадение направления
                if ghost_signal['type'] == ott_signal['type']:
                    combined_signal = {
                        'time': time,
                        'type': ghost_signal['type'],
                        'price': ghost_signal['price'],
                        'ghost_signal': ghost_signal,
                        'ott_signal': ott_signal,
                        'confidence': self.calculate_confidence(ghost_signal, ott_signal),
                        'strategy': 'combined'
                    }
                    combined_signals.append(combined_signal)
                    
                    # Обновляем историю сигналов
                    self.signal_history.append({
                        'time': time,
                        'ghost_type': ghost_signal['type'],
                        'ott_type': ott_signal['type'],
                        'combined': True,
                        'confidence': combined_signal['confidence']
                    })
                else:
                    # Противоречивые сигналы
                    self.signal_history.append({
                        'time': time,
                        'ghost_type': ghost_signal['type'],
                        'ott_type': ott_signal['type'],
                        'combined': False,
                        'confidence': 0
                    })
            
            # Если есть сигнал только от одной стратегии
            elif ghost_signal:
                self.signal_history.append({
                    'time': time,
                    'ghost_type': ghost_signal['type'],
                    'ott_type': None,
                    'combined': False,
                    'confidence': 0
                })
            elif ott_signal:
                self.signal_history.append({
                    'time': time,
                    'ghost_type': None,
                    'ott_type': ott_signal['type'],
                    'combined': False,
                    'confidence': 0
                })
        
        return combined_signals
    
    def calculate_confidence(self, ghost_signal, ott_signal):
        """
        Рассчитывает уверенность в сигнале на основе силы обоих индикаторов
        """
        # Сила сигнала GhostTangent (на основе pivot strength)
        ghost_strength = ghost_signal.get('pivot_strength', 0.5)
        
        # Сила сигнала OTT (на основе signal_strength)
        ott_strength = ott_signal.get('signal_strength', 1.0)
        
        # Нормализуем значения
        ghost_normalized = min(ghost_strength / 2.0, 1.0)  # Максимум 2.0
        ott_normalized = min(ott_strength / 5.0, 1.0)      # Максимум 5%
        
        # Среднее значение с весами
        confidence = (ghost_normalized * 0.6 + ott_normalized * 0.4)
        
        return round(confidence * 100, 2)  # В процентах
    
    def get_strategy_stats(self):
        """
        Возвращает статистику работы стратегий
        """
        if not self.signal_history:
            return {
                'total_signals': 0,
                'combined_signals': 0,
                'ghost_only': 0,
                'ott_only': 0,
                'conflicting': 0,
                'avg_confidence': 0
            }
        
        total = len(self.signal_history)
        combined = sum(1 for s in self.signal_history if s['combined'])
        ghost_only = sum(1 for s in self.signal_history if s['ghost_type'] and not s['ott_type'])
        ott_only = sum(1 for s in self.signal_history if s['ott_type'] and not s['ghost_type'])
        conflicting = sum(1 for s in self.signal_history if s['ghost_type'] and s['ott_type'] and not s['combined'])
        
        avg_confidence = sum(s['confidence'] for s in self.signal_history if s['combined']) / combined if combined > 0 else 0
        
        return {
            'total_signals': total,
            'combined_signals': combined,
            'ghost_only': ghost_only,
            'ott_only': ott_only,
            'conflicting': conflicting,
            'avg_confidence': round(avg_confidence, 2),
            'combined_percentage': round(combined / total * 100, 2) if total > 0 else 0
        }
    
    def get_indicators_data(self, df):
        """
        Возвращает данные обоих индикаторов для отображения на графике
        """
        # Данные GhostTangent
        ghost_data = self.ghost_strategy.get_pivot_data(df)
        
        # Данные OTT
        ott_data = self.ott_strategy.get_ott_data(df)
        
        # Объединяем данные
        combined_data = pd.concat([ghost_data, ott_data], axis=1)
        
        return combined_data
    
    def analyze_market_conditions(self, df):
        """
        Анализирует рыночные условия на основе обоих индикаторов
        """
        if len(df) < 20:
            return {'trend': 'unknown', 'volatility': 'unknown', 'recommendation': 'insufficient_data'}
        
        # Анализ тренда по OTT
        ott_data = self.ott_strategy.get_ott_data(df)
        recent_ott = ott_data['ott'].tail(10)
        ott_trend = 'bullish' if recent_ott.iloc[-1] > recent_ott.iloc[0] else 'bearish'
        
        # Анализ волатильности по GhostTangent
        ghost_data = self.ghost_strategy.get_pivot_data(df)
        recent_pivots = ghost_data.tail(20)
        pivot_heights = recent_pivots[recent_pivots['pivot_high'] > 0]['high']
        pivot_lows = recent_pivots[recent_pivots['pivot_low'] > 0]['low']
        
        if len(pivot_heights) > 0 and len(pivot_lows) > 0:
            avg_range = (pivot_heights.mean() - pivot_lows.mean()) / df['close'].mean() * 100
            volatility = 'high' if avg_range > 5 else 'low' if avg_range < 2 else 'medium'
        else:
            volatility = 'unknown'
        
        # Рекомендации
        if ott_trend == 'bullish' and volatility == 'medium':
            recommendation = 'favorable_for_buy'
        elif ott_trend == 'bearish' and volatility == 'medium':
            recommendation = 'favorable_for_sell'
        elif volatility == 'high':
            recommendation = 'high_risk'
        elif volatility == 'low':
            recommendation = 'low_opportunity'
        else:
            recommendation = 'neutral'
        
        return {
            'trend': ott_trend,
            'volatility': volatility,
            'recommendation': recommendation,
            'ott_current': float(ott_data['ott'].iloc[-1]),
            'ott_color': ott_data['ott_color'].iloc[-1]
        } 