#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_fetcher import DataFetcher
from app.services.signal_generator import SignalGenerator
import pandas as pd

async def debug_confirmed_buy():
    print("=== Debugging Confirmed Buy Logic for WES.AX ===")
    
    data_fetcher = DataFetcher()
    signal_gen = SignalGenerator()
    
    # Fetch data for WES
    data = await data_fetcher.fetch_stock_data('WES.AX', period='60d', interval='1d')
    if data is None or data.empty:
        print("Could not fetch data")
        return
        
    print(f"Data fetched: {len(data)} rows")
    print(f"Latest close: {data['close'].iloc[-1]}")
    
    # Manually check all conditions
    if len(data) < 50:
        print("FAIL: Not enough data (need 50+ candles)")
        return
        
    # Calculate indicators
    ema_5 = signal_gen.calculate_ema(data['close'], 5)
    ema_20 = signal_gen.calculate_ema(data['close'], 20)
    sma_50 = signal_gen.calculate_sma(data['close'], 50)
    rsi = signal_gen.calculate_rsi(data['close'])
    macd_data = signal_gen.calculate_macd(data['close'])
    macd_line = macd_data['macd']
    signal_line = macd_data['signal']
    
    # Current values
    current_open = float(data['open'].iloc[-1])
    current_close = float(data['close'].iloc[-1])
    current_ema_5 = float(ema_5.iloc[-1])
    current_ema_20 = float(ema_20.iloc[-1])
    current_sma_50 = float(sma_50.iloc[-1])
    current_rsi = float(rsi.iloc[-1])
    current_macd = float(macd_line.iloc[-1])
    current_signal = float(signal_line.iloc[-1])
    
    print(f"\n=== Current Values ===")
    print(f"Open: {current_open:.2f}")
    print(f"Close: {current_close:.2f}")
    print(f"5 EMA: {current_ema_5:.2f}")
    print(f"20 EMA: {current_ema_20:.2f}")
    print(f"50 SMA: {current_sma_50:.2f}")
    print(f"RSI: {current_rsi:.2f}")
    print(f"MACD: {current_macd:.4f}")
    print(f"Signal Line: {current_signal:.4f}")
    
    # Check each condition
    print(f"\n=== Condition Analysis ===")
    
    # Condition 1: EMA crossover in last 9 days
    ema_crossover_detected = False
    for i in range(2, min(10, len(data))):
        prev_ema_5 = float(ema_5.iloc[-(i+1)])
        prev_ema_20 = float(ema_20.iloc[-(i+1)])
        curr_ema_5 = float(ema_5.iloc[-i])
        curr_ema_20 = float(ema_20.iloc[-i])
        
        if prev_ema_5 <= prev_ema_20 and curr_ema_5 > curr_ema_20:
            ema_crossover_detected = True
            print(f"1. EMA Crossover: PASS (found {i} days ago)")
            break
    
    if not ema_crossover_detected:
        print("1. EMA Crossover: FAIL (no crossover in last 9 days)")
    
    # Condition 2: Current candle above EMAs
    above_emas = current_open > current_ema_5 and current_open > current_ema_20 and current_close > current_ema_5 and current_close > current_ema_20
    print(f"2. Above EMAs: {'PASS' if above_emas else 'FAIL'} (open: {current_open:.2f} > {current_ema_5:.2f} and {current_ema_20:.2f}, close: {current_close:.2f} > {current_ema_5:.2f} and {current_ema_20:.2f})")
    
    # Condition 3: Above 50 SMA
    above_sma = current_close > current_sma_50
    print(f"3. Above SMA 50: {'PASS' if above_sma else 'FAIL'} (close: {current_close:.2f} > {current_sma_50:.2f})")
    
    # Condition 4: Volume (using ratio method like reference)
    if 'volume' in data.columns:
        volume_5_day_avg = data['volume'].rolling(window=5, min_periods=1).mean()
        volume_50_day_avg = data['volume'].rolling(window=50, min_periods=1).mean()
        volume_ratio = volume_5_day_avg / volume_50_day_avg
        current_volume_ratio = float(volume_ratio.iloc[-1])
        volume_good = current_volume_ratio > 1.0
        print(f"4. Volume: {'PASS' if volume_good else 'FAIL'} (ratio: {current_volume_ratio:.3f} > 1.0)")
    else:
        volume_good = False
        current_volume_ratio = 0.0
        print("4. Volume: FAIL (no volume data)")
    
    # Condition 5: RSI > 50
    rsi_good = current_rsi > 50
    print(f"5. RSI > 50: {'PASS' if rsi_good else 'FAIL'} ({current_rsi:.2f})")
    
    # Condition 6: MACD > Signal Line
    macd_good = current_macd > current_signal
    print(f"6. MACD > Signal: {'PASS' if macd_good else 'FAIL'} ({current_macd:.4f} > {current_signal:.4f})")
    
    # Final result
    all_conditions = [ema_crossover_detected, above_emas, above_sma, volume_good, rsi_good, macd_good]
    passed_count = sum(all_conditions)
    
    print(f"\n=== Final Result ===")
    print(f"Conditions passed: {passed_count}/6")
    
    if passed_count == 6:
        print("CONFIRMED BUY SIGNAL DETECTED!")
    else:
        print("No confirmed buy signal")

if __name__ == "__main__":
    asyncio.run(debug_confirmed_buy())