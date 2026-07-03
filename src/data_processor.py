import os
import pandas as pd

def clean_and_format(raw_data: dict) -> pd.DataFrame:
    if not raw_data or "Time Series (Daily)" not in raw_data:
        return pd.DataFrame()
        
    # 提取核心时间序列
    time_series = raw_data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(time_series, orient='index')
    
    # 清洗列名 (去除非法字符与序号)
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume"
    })
    
    # 强制转换数据类型
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # 按照时间轴正序排列 (从过去到现在)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=True)
    
    return df

def save_to_csv(df: pd.DataFrame, symbol: str, output_dir: str = "data"):
    """
    将计算完备的数字资产账本保存至本地
    """
    if df is None or df.empty:
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_path = os.path.join(output_dir, f"{symbol}_backtest_ledger.csv")
    df.to_csv(file_path)
    print(f"[数据落盘] 历史账本已成功写入: {file_path}")