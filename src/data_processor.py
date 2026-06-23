import pandas as pd 
import os 
from typing import Optional
def clean_and_format(raw_data: Optional[dict]) -> pd.DataFrame: #定义一个函数clean_and_format，接受一个可选的字典类型参数raw_data，并返回一个pandas DataFrame对象
    if not raw_data:  #如果raw_data为None或空，则打印错误信息并返回一个空的DataFrame对象
        return pd.DataFrame()
    #将raw_data字典转换为pandas DataFrame对象，orient参数设置为'index'表示字典的键将成为DataFrame的行索引
    df = pd.DataFrame.from_dict(raw_data, orient='index') 
    #将DataFrame的列名设置为'open'、'high'、'low'、'close'和'volume'
    df.columns = ['open', 'high', 'low', 'close', 'volume']  
    #将DataFrame中的所有数据类型转换为float类型
    df = df.astype(float)
    #将DataFrame的行索引转换为datetime类型
    df.index = pd.to_datetime(df.index)
    #按照行索引（日期）进行升序排序
    df.sort_index(ascending=True, inplace=True)
    print("数据清洗和格式化完成。")
    return df  #返回清洗和格式化后的DataFrame对象

def save_to_csv(df: pd.DataFrame, symbol: str, output_dir: str = "data") -> None:
    if df.empty:
        print(f"[数据存储]{symbol} 数据为空，取消保持。")
        return
    #自动创建文件夹：如果本地没有 'data' 文件夹，程序会自动建一个
    os.makedirs(output_dir, exist_ok=True)
    #拼接完整的文件存储路径，例如 "data/AAPL_daily.csv"
    file_path = os.path.join(output_dir, f"{symbol.upper()}_daily.csv")
    #保存为 CSV，保留时间索引列
    df.to_csv(file_path, index_label="date")
    print(f"数据存储{symbol} 数据以安全导入: {file_path}")

# ==========================================
# 本地测试模块（独立验证清洗与存储）
# ==========================================
if __name__ == "__main__":
    print("--- 开始测试数据清洗与存储模块 ---")
    mock_raw_data = {
        "2024-06-01": {"1. open": "150.00", "2. high": "155.00", "3. low": "149.00", "4. close": "154.00", "5. volume": "1000000"},
        "2024-06-02": {"1. open": "154.00", "2. high": "158.00", "3. low": "153.00", "4. close": "157.00", "5. volume": "1200000"}
    }
    cleaned_df = clean_and_format(mock_raw_data)
    print("\n📊 清洗后的 DataFrame 预览:")
    print(cleaned_df)
    print(f"索引类型: {cleaned_df.index.dtype}, 收盘价类型: {cleaned_df['close'].dtype}")
    save_to_csv(cleaned_df, "TEST_STOCK")