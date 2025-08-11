"""
Signal Detectors Module
Contains all signal detection algorithms for trading analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

from app.models import SignalType, SignalStrength
from app.services.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class SignalDetectors:
    """Collection of signal detection algorithms"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def detect_ema_crossover_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect EMA crossover signals (12 EMA crosses 26 EMA)"""
        if len(data) < 26:
            return None
        
        try:
            ema_12 = self.indicators.calculate_ema(data['close'], 12)
            ema_26 = self.indicators.calculate_ema(data['close'], 26)
            rsi = self.indicators.calculate_rsi(data['close'])
            
            # Get last few values
            current_ema_12 = ema_12.iloc[-1]
            current_ema_26 = ema_26.iloc[-1]
            prev_ema_12 = ema_12.iloc[-2]
            prev_ema_26 = ema_26.iloc[-2]
            current_rsi = rsi.iloc[-1]
            
            # Check for crossover
            bullish_crossover = (prev_ema_12 <= prev_ema_26) and (current_ema_12 > current_ema_26)
            bearish_crossover = (prev_ema_12 >= prev_ema_26) and (current_ema_12 < current_ema_26)
            
            if bullish_crossover and current_rsi < 70:  # Not overbought
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.MODERATE,
                    'confidence_score': 0.7,
                    'details': {
                        'type': 'ema_crossover',
                        'ema_12': current_ema_12,
                        'ema_26': current_ema_26,
                        'rsi': current_rsi,
                        'reason': 'Bullish EMA crossover with RSI confirmation'
                    }
                }
            
            elif bearish_crossover and current_rsi > 30:  # Not oversold
                return {
                    'signal_type': SignalType.SELL,
                    'signal_strength': SignalStrength.MODERATE,
                    'confidence_score': 0.7,
                    'details': {
                        'type': 'ema_crossover',
                        'ema_12': current_ema_12,
                        'ema_26': current_ema_26,
                        'rsi': current_rsi,
                        'reason': 'Bearish EMA crossover with RSI confirmation'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in EMA crossover detection: {str(e)}")
            return None
    
    def detect_golden_cross_signal(self, data: pd.DataFrame) -> Optional[Dict]:
        """Detect Golden Cross signal (50 SMA crosses above 200 SMA)"""
        if len(data) < 200:
            return None
        
        try:
            sma_50 = self.indicators.calculate_sma(data['close'], 50)
            sma_200 = self.indicators.calculate_sma(data['close'], 200)
            
            current_sma_50 = sma_50.iloc[-1]
            current_sma_200 = sma_200.iloc[-1]
            prev_sma_50 = sma_50.iloc[-2]
            prev_sma_200 = sma_200.iloc[-2]
            
            # Golden Cross: 50 SMA crosses above 200 SMA
            golden_cross = (prev_sma_50 <= prev_sma_200) and (current_sma_50 > current_sma_200)
            
            # Death Cross: 50 SMA crosses below 200 SMA
            death_cross = (prev_sma_50 >= prev_sma_200) and (current_sma_50 < current_sma_200)
            
            if golden_cross:
                return {
                    'signal_type': SignalType.BUY,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.85,
                    'details': {
                        'type': 'golden_cross',
                        'sma_50': current_sma_50,
                        'sma_200': current_sma_200,
                        'reason': 'Golden Cross - 50 SMA crossed above 200 SMA'
                    }
                }
            
            elif death_cross:
                return {
                    'signal_type': SignalType.SELL,
                    'signal_strength': SignalStrength.STRONG,
                    'confidence_score': 0.85,
                    'details': {
                        'type': 'death_cross',
                        'sma_50': current_sma_50,
                        'sma_200': current_sma_200,
                        'reason': 'Death Cross - 50 SMA crossed below 200 SMA'
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error in Golden Cross detection: {str(e)}")
            return None