import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame, short_window: int = 5, long_window: int = 10, 
                         trend_window: int = 60, rsi_window: int = 14,
                         macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9,
                         bb_window: int = 20, bb_std: float = 2.0,
                         kdj_window: int = 9, atr_window: int = 14) -> pd.DataFrame:
    if df is None or df.empty:
        return df
        
    df_feat = df.copy() 
    
    # 均线族
    df_feat['short_ma'] = df_feat['close'].rolling(window=int(short_window)).mean()
    df_feat['long_ma'] = df_feat['close'].rolling(window=int(long_window)).mean()
    df_feat['trend_ma'] = df_feat['close'].rolling(window=int(trend_window)).mean()
    
    # RSI 动量
    delta = df_feat['close'].diff()
    gain, loss = delta.copy(), delta.copy()
    gain[gain < 0] = 0.0
    loss[loss > 0] = 0.0
    loss = abs(loss)
    avg_gain = gain.rolling(window=int(rsi_window), min_periods=int(rsi_window)).mean()
    avg_loss = loss.rolling(window=int(rsi_window), min_periods=int(rsi_window)).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df_feat['rsi'] = 100 - (100 / (1 + rs))
    df_feat['rsi'] = df_feat['rsi'].fillna(50)  
    
    # MACD
    df_feat['macd_ema_fast'] = df_feat['close'].ewm(span=int(macd_fast), adjust=False).mean()
    df_feat['macd_ema_slow'] = df_feat['close'].ewm(span=int(macd_slow), adjust=False).mean()
    df_feat['macd_diff'] = df_feat['macd_ema_fast'] - df_feat['macd_ema_slow']
    df_feat['macd_dea'] = df_feat['macd_diff'].ewm(span=int(macd_signal), adjust=False).mean()
    df_feat['macd_hist'] = df_feat['macd_diff'] - df_feat['macd_dea']
    
    # 布林带
    df_feat['bb_mid'] = df_feat['close'].rolling(window=int(bb_window)).mean()
    df_feat['bb_std'] = df_feat['close'].rolling(window=int(bb_window)).std()
    df_feat['bb_upper'] = df_feat['bb_mid'] + (bb_std * df_feat['bb_std'])
    df_feat['bb_lower'] = df_feat['bb_mid'] - (bb_std * df_feat['bb_std'])
    
    # KDJ
    low_min = df_feat['low'].rolling(window=int(kdj_window)).min()
    high_max = df_feat['high'].rolling(window=int(kdj_window)).max()
    rsv = (df_feat['close'] - low_min) / (high_max - low_min).replace(0, np.nan) * 100
    df_feat['kdj_k'] = rsv.ewm(com=2, adjust=False).mean()
    df_feat['kdj_d'] = df_feat['kdj_k'].ewm(com=2, adjust=False).mean()
    df_feat['kdj_j'] = 3 * df_feat['kdj_k'] - 2 * df_feat['kdj_d']
    
    # ATR
    high_low = df_feat['high'] - df_feat['low']
    high_close = (df_feat['high'] - df_feat['close'].shift(1)).abs()
    low_close = (df_feat['low'] - df_feat['close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df_feat['atr'] = tr.rolling(window=int(atr_window)).mean()
    
    return df_feat

def generate_signals(df: pd.DataFrame, enabled_factors: dict) -> pd.DataFrame:
    if df.empty:
        return df
        
    df_sig = df.copy()
    df_sig['position'] = 0.0
    df_sig['signal'] = 0.0
    
    # 全因子防御性卡口检查：如果用户开启了某因子，但数据列不存在，强制关闭该因子
    for factor, col in [('MA','short_ma'), ('TREND','trend_ma'), ('RSI','rsi'), ('MACD','macd_hist'), ('BB','bb_upper'), ('KDJ','kdj_k'), ('ATR','atr')]:
        if enabled_factors.get(factor, False) and col not in df_sig.columns:
            enabled_factors[factor] = False
            
    # 全空防御
    if not any(enabled_factors.values()):
        print("[系统警告] 你关闭了所有策略因子！系统将保持绝对空仓观望。")
        return df_sig
        
    # 底层历史平移项准备
    p_short1, p_short2 = df_sig['short_ma'].shift(1), df_sig['short_ma'].shift(2)
    p_long1, p_long2 = df_sig['long_ma'].shift(1), df_sig['long_ma'].shift(2)
    p_k1, p_k2 = df_sig['kdj_k'].shift(1), df_sig['kdj_k'].shift(2)
    p_d1, p_d2 = df_sig['kdj_d'].shift(1), df_sig['kdj_d'].shift(2)
    p_close1 = df_sig['close'].shift(1)
    p_trend1 = df_sig['trend_ma'].shift(1)
    p_rsi1 = df_sig['rsi'].shift(1)
    p_macd_hist1 = df_sig['macd_hist'].shift(1)
    p_bb_upper1 = df_sig['bb_upper'].shift(1)
    p_bb_mid1 = df_sig['bb_mid'].shift(1)
    p_atr1 = df_sig['atr'].shift(1)
    
    current_position = 0.0
    highest_close_since_entry = 0.0
    positions, signals = [], []
    
    for idx in range(len(df_sig)):
        if idx < 2:
            positions.append(0.0)
            signals.append(0.0)
            continue
            
        # 1.动态构建开仓触发器 (MA 或 KDJ 产生金叉)
        # 如果均开启，任意一个金叉即可触发；如果均未开启，则默认允许触发（完全靠过滤因子控制）
        has_trigger_defined = enabled_factors.get('MA', False) or enabled_factors.get('KDJ', False)
        if has_trigger_defined:
            ma_gold = (p_short1.iloc[idx] > p_long1.iloc[idx]) and (p_short2.iloc[idx] <= p_long2.iloc[idx]) if enabled_factors['MA'] else False
            kdj_gold = (p_k1.iloc[idx] > p_d1.iloc[idx]) and (p_k2.iloc[idx] <= p_d2.iloc[idx]) if enabled_factors['KDJ'] else False
            trigger_buy = ma_gold or kdj_gold
        else:
            trigger_buy = True 

        # 2.动态构建开仓过滤器 (必须全部通过 AND 校验)
        filter_pass = True
        if enabled_factors.get('TREND', False) and not (p_close1.iloc[idx] > p_trend1.iloc[idx]):
            filter_pass = False
        if enabled_factors.get('RSI', False) and not (p_rsi1.iloc[idx] < 65):
            filter_pass = False
        if enabled_factors.get('MACD', False) and not (p_macd_hist1.iloc[idx] > 0):
            filter_pass = False
        if enabled_factors.get('BB', False) and not (p_close1.iloc[idx] < p_bb_upper1.iloc[idx]):
            filter_pass = False

        # 3.动态构建平仓/止损触发器 (任何一个触发 OR 校验)
        trigger_sell = False
        if enabled_factors.get('MA', False) and ((p_short1.iloc[idx] < p_long1.iloc[idx]) and (p_short2.iloc[idx] >= p_long2.iloc[idx])):
            trigger_sell = True
        if enabled_factors.get('KDJ', False) and ((p_k1.iloc[idx] < p_d1.iloc[idx]) and (p_k2.iloc[idx] >= p_d2.iloc[idx])):
            trigger_sell = True
        if enabled_factors.get('TREND', False) and (p_close1.iloc[idx] < p_trend1.iloc[idx]):
            trigger_sell = True
        if enabled_factors.get('RSI', False) and (p_rsi1.iloc[idx] > 80):
            trigger_sell = True
        if enabled_factors.get('BB', False) and (p_close1.iloc[idx] < p_bb_mid1.iloc[idx]):
            trigger_sell = True
            
        # ATR 追踪止损风控
        if current_position == 1.0:
            highest_close_since_entry = max(highest_close_since_entry, p_close1.iloc[idx])
            if enabled_factors.get('ATR', False) and (p_close1.iloc[idx] < (highest_close_since_entry - 3.0 * p_atr1.iloc[idx])):
                trigger_sell = True

        # 4.状态机流转执行
        signal = 0.0
        if current_position == 0.0:
            if trigger_buy and filter_pass:
                current_position = 1.0
                signal = 1.0
                highest_close_since_entry = p_close1.iloc[idx]
        elif current_position == 1.0:
            if trigger_sell:
                current_position = 0.0
                signal = -1.0
                highest_close_since_entry = 0.0
                
        positions.append(current_position)
        signals.append(signal)
        
    df_sig['position'] = positions
    df_sig['signal'] = signals
    df_sig['signal'] = df_sig['signal'].astype(int)
    
    return df_sig