import pandas as pd 
import os 
from typing import Optional

def clean_and_format(raw_data: Optional[dict]) -> pd.DataFrame:
    """
    清洗和格式化 AlphaVantage 原生字典数据，转换为标准时序 DataFrame
    """
    if not raw_data:
        print("⚠️ [数据清洗] 收到空数据，返回空 DataFrame。")
        return pd.DataFrame()
        
    # 将字典转换为 DataFrame，行索引为日期
    df = pd.DataFrame.from_dict(raw_data, orient='index') 
    
    # 🌟 优化点：改用显式字典映射重命名，比直接强行赋值 columns 更安全
    # 这样能精准匹配 AlphaVantage 的原生列名，防止字段顺序错乱
    rename_map = {
        '1. open': 'open', 
        '2. high': 'high', 
        '3. low': 'low', 
        '4. close': 'close', 
        '5. volume': 'volume'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # 确保转换数据类型
    df = df.astype(float)
    
    # 将行索引转换为标准的 DatetimeIndex
    df.index = pd.to_datetime(df.index)
    
    # 按照日期进行升序排序（从历史走到今天）
    df.sort_index(ascending=True, inplace=True)
    
    print("📊 [数据清洗] 基础行情行情数据清洗和格式化完成。")
    return df

def save_to_csv(df: pd.DataFrame, symbol: str, output_dir: str = "data") -> None:
    """
    动态全量数据落盘函数：自动保留内存中所有新增的指标列、信号列与回测账本列
    """
    if df is None or df.empty:
        print(f"⚠️ [数据存储] {symbol} 数据为空，取消保存。")
        return
        
    # 自动创建文件夹（如果本地没有 'data' 文件夹，程序会自动新建）
    os.makedirs(output_dir, exist_ok=True)
    
    # 拼接完整的文件存储路径
    file_path = os.path.join(output_dir, f"{symbol.upper()}_daily.csv")
    
    # 🌟 核心保证：直接对整体 df 进行导出，不加任何列过滤
    # index_label="date" 会把行索引在 CSV 中命名为 "date" 列，且最右侧会动态长出回测的所有列
    df.to_csv(file_path, index_label="date")
    print(f"💾 [数据存储] {symbol} 终极数字化资产矩阵已安全导入: {file_path}")

# ==========================================
# 本地测试模块（独立验证清洗与存储）
# ==========================================
if __name__ == "__main__":
    print("--- 开始测试数据清洗与存储模块 ---")
    mock_raw_data = {
        "2026-06-01": {"1. open": "150.00", "2. high": "155.00", "3. low": "149.00", "4. close": "154.00", "5. volume": "1000000"},
        "2026-06-02": {"1. open": "154.00", "2. high": "158.00", "3. low": "153.00", "4. close": "157.00", "5. volume": "1200000"}
    }
    cleaned_df = clean_and_format(mock_raw_data)
    print("\n📊 清洗后的 DataFrame 预览:")
    print(cleaned_df)
    print(f"索引类型: {cleaned_df.index.dtype}, 收盘价类型: {cleaned_df['close'].dtype}")
    
    # 测试保存
    save_to_csv(cleaned_df, "TEST_STOCK")