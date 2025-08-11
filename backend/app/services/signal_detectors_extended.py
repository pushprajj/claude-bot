"""
Extended Signal Detectors Module
Additional signal detection algorithms for comprehensive trading analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging
from datetime import datetime, date

from app.models import SignalType, SignalStrength
from app.services.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class ExtendedSignalDetectors:
    """Extended collection of signal detection algorithms"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def detect_sma_volume_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect 200 SMA cross with higher volume"""
        if len(data) < 200:
            return None
        
        try:
            sma_200 = self.indicators.calculate_sma(data['close'], 200)
            volume_avg = self.indicators.calculate_sma(data['volume'], 20)
            
            current_price = data['close'].iloc[-1]
            current_sma_200 = sma_200.iloc[-1]
            prev_price = data['close'].iloc[-2]
            prev_sma_200 = sma_200.iloc[-2]
            current_volume = data['volume'].iloc[-1]
            avg_volume = volume_avg.iloc[-1]
            
            # Price crosses above 200 SMA with higher volume
            bullish_cross = (prev_price <= prev_sma_200) and (current_price > current_sma_200)
            bearish_cross = (prev_price >= prev_sma_200) and (current_price < current_sma_200)
            high_volume = current_volume > (avg_volume * 1.2)  # 20% above average
            
            if bullish_cross and high_volume:
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.8,
                    'details': {
                        'type': 'sma_volume_breakout',
                        'price': current_price,
                        'sma_200': current_sma_200,
                        'volume': current_volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': current_volume / avg_volume,
                        'reason': 'Price crossed above 200 SMA with high volume'
                    }
                }
            
            elif bearish_cross and high_volume:
                return {
                    'signal_type': SignalType.SELL,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.8,
                    'details': {
                        'type': 'sma_volume_breakdown',
                        'price': current_price,
                        'sma_200': current_sma_200,
                        'volume': current_volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': current_volume / avg_volume,
                        'reason': 'Price crossed below 200 SMA with high volume'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SMA volume detection: {str(e)}")
            return None
    
    def detect_sma_above_50_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Simple test signal: SMA 50 above current price"""
        if len(data) < 50:
            return None
        
        try:
            sma_50 = self.indicators.calculate_sma(data['close'], 50)
            current_price = data['close'].iloc[-1]
            current_sma_50 = sma_50.iloc[-1]
            prev_price = data['close'].iloc[-2]
            prev_sma_50 = sma_50.iloc[-2]
            
            # Check if price crossed above SMA 50
            crossed_above = (prev_price <= prev_sma_50) and (current_price > current_sma_50)
            
            # Or if price is above SMA 50 and trending up
            above_sma = current_price > current_sma_50
            trending_up = current_price > prev_price
            
            if crossed_above or (above_sma and trending_up):
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.WEAK if above_sma else SignalStrength.MODERATE,
                    'confidence_score': 0.5 if above_sma else 0.65,
                    'details': {
                        'type': 'sma_50_above',
                        'price': current_price,
                        'sma_50': current_sma_50,
                        'crossed_above': crossed_above,
                        'reason': 'Price crossed above SMA 50' if crossed_above else 'Price above SMA 50 and trending up'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SMA 50 detection: {str(e)}")
            return None
    
    def detect_confirmed_buy_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        Detect confirmed buy signal with specific conditions:
        1. 5 EMA crossed 20 EMA in the last 5 days, excluding latest closed candle
        2. Last closed candle (both open and close prices) above both 5 EMA and 20 EMA
        3. Closed price of last candle above 50 SMA
        4. Average Volume for latest 5 candles > average of last 50 candles
        5. RSI above 50
        6. MACD positive on the last candle
        """
        if len(data) < 50:  # Need at least 50 candles for all calculations
            return None
        
        try:
            # Calculate indicators
            ema_5 = self.indicators.calculate_ema(data['close'], 5)
            ema_20 = self.indicators.calculate_ema(data['close'], 20)
            sma_50 = self.indicators.calculate_sma(data['close'], 50)
            rsi = self.indicators.calculate_rsi(data['close'])
            macd_data = self.indicators.calculate_macd(data['close'])
            macd_line = macd_data['macd']
            signal_line = macd_data['signal']
            
            # Current values (last closed candle) - convert to native Python types
            current_open = float(data['open'].iloc[-1])
            current_close = float(data['close'].iloc[-1])
            current_ema_5 = float(ema_5.iloc[-1])
            current_ema_20 = float(ema_20.iloc[-1])
            current_sma_50 = float(sma_50.iloc[-1])
            current_rsi = float(rsi.iloc[-1])
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(signal_line.iloc[-1])
            
            # Get the signal date - this will be overridden by the signal generator with validated date
            signal_date = date.today()
            
            # Calculate volume ratios
            if 'volume' in data.columns:
                volume_5_day_avg = data['volume'].rolling(window=5, min_periods=1).mean()
                volume_50_day_avg = data['volume'].rolling(window=50, min_periods=1).mean()
                volume_ratio = volume_5_day_avg / volume_50_day_avg
                current_volume_ratio = float(volume_ratio.iloc[-1])
            else:
                current_volume_ratio = 0.0
            
            # Condition 1: 5 EMA crossed 20 EMA in last 10 candles (days -11 to -2, excluding latest)
            # This matches the reference implementation exactly
            ema_crossover_detected = False
            current_above = current_ema_5 > current_ema_20
            
            # Find cross points in window [-11, -2] (excluding current candle at -1)
            cross_points = []
            for j in range(-11, -1):  # Check indices -11, -10, -9, -8, -7, -6, -5, -4, -3, -2
                if len(data) > abs(j):  # Ensure we have enough data
                    curr_ema_5 = float(ema_5.iloc[j])
                    curr_ema_20 = float(ema_20.iloc[j])
                    prev_ema_5 = float(ema_5.iloc[j-1]) if len(data) > abs(j-1) else curr_ema_5
                    prev_ema_20 = float(ema_20.iloc[j-1]) if len(data) > abs(j-1) else curr_ema_20
                    
                    # Bullish crossover: 5 EMA crosses above 20 EMA
                    if curr_ema_5 > curr_ema_20 and prev_ema_5 <= prev_ema_20:
                        cross_points.append(j)
            
            # Only consider if there is a cross and we're currently above
            if cross_points and current_above:
                most_recent_cross = max(cross_points)
                # Match reference: check if most recent cross is in [-2, -3, -4, -5, -6, -7, -8, -9, -10, -11]
                if most_recent_cross in [-2, -3, -4, -5, -6, -7, -8, -9, -10, -11]:
                    ema_crossover_detected = True
            
            # Condition 2: Last closed candle (open and close) above both EMAs
            price_above_emas = (current_open > current_ema_5 and current_open > current_ema_20 and
                               current_close > current_ema_5 and current_close > current_ema_20)
            
            # Condition 3: Close price above 50 SMA
            price_above_sma50 = current_close > current_sma_50
            
            # Condition 4: Volume ratio > 1.0
            volume_confirmation = current_volume_ratio > 1.0
            
            # Condition 5: RSI above 50
            rsi_bullish = current_rsi > 50
            
            # Condition 6: MACD above Signal Line
            macd_cross = current_macd > current_signal
            
            # Define all core conditions
            core_conditions = [
                ema_crossover_detected,
                price_above_emas,
                price_above_sma50,
                rsi_bullish,
                macd_cross
            ]
            
            if all(core_conditions + [volume_confirmation]):  # All 6 conditions including volume
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.95,
                    'signal_date': signal_date,
                    'details': {
                        'type': 'confirmed_buy_volume',
                        'reason': 'All buy conditions met (volume confirmed)',
                        'price': float(current_close),
                        'open_price': float(current_open),
                        'ema_5': float(current_ema_5),
                        'ema_20': float(current_ema_20),
                        'sma_50': float(current_sma_50),
                        'rsi': float(current_rsi),
                        'macd': float(current_macd),
                        'volume_ratio': float(current_volume_ratio),
                        'conditions_met': 6,
                        'ema_crossover': ema_crossover_detected,
                        'price_above_emas': price_above_emas,
                        'price_above_sma50': price_above_sma50,
                        'volume_confirmation': volume_confirmation,
                        'rsi_bullish': rsi_bullish,
                        'macd_cross': macd_cross,
                        'reason': 'Confirmed buy signal - all 6 conditions met: 5EMA/20EMA crossover in last 5 days, price above EMAs, price above 50 SMA, volume spike, RSI > 50, MACD > Signal Line'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in confirmed buy detection: {str(e)}")
            return None