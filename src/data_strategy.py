import pandas as pd
import numpy as np

def calculate_indicators(df: pd.DataFrame, short_window: int = 5, long_window: int = 10) -> pd.DataFrame:
    if df.empty:
        print("指标计算]收到空数据, 无法计算指标。")
        return df
    df_feat = df.copy() #如果不加 .copy()，后续直接往 df 里新增列时，Pandas 会警告。显式复制一份可以确保内存安全。
    df_feat['short_ma'] = df_feat['close'].rolling(window=short_window).mean()
    df_feat['long_ma'] = df_feat['close'].rolling(window=long_window).mean()
    return df_feat
def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or 'short_ma' not in df.columns or 'long_ma' not in df.columns:
        print("[信号生成] 缺失必要指标列，取消信号生成。")
        return df
    df_sig = df.copy()
    df_sig['position'] = np.where(df_sig['short_ma'] > df_sig['long_ma'], 1, 0) #构建状态列 position（1代表短期在上，0代表短期在下）
    df_sig['signal'] = df_sig['position'].diff() #利用一阶差分（diff）捕捉状态切换的“那一瞬间”
    df_sig['signal'] = df_sig['signal'].fillna(0).astype(int) #数据清洗，将缺失值填充为 0，并强转为标准的整型信号
    return df_sig

# 本地测试模块（离线验证指标与信号逻辑）
if __name__ == "__main__":
    print("--- 开始测试指标与信号生成模块 ---")
    # 模拟 12 天的股价上涨后下跌的行情数据
    mock_data = {
        'close': [100, 101, 102, 104, 106, 108, 107, 105, 103, 101, 99, 98]
    }
    # 创建一个以连续日期为索引的测试表
    dates = pd.date_range(start="2026-06-01", periods=12)
    test_df = pd.DataFrame(mock_data, index=dates)
    df_with_indicators = calculate_indicators(test_df, short_window=2, long_window=5)
    df_with_signals = generate_signals(df_with_indicators)
    print("\n📊 策略信号特征表预览 (展示收盘价、均线、持仓状态、交易信号):")
    print(df_with_signals[['close', 'short_ma', 'long_ma', 'position', 'signal']])