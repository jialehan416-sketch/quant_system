import os
import json
import pandas as pd
import numpy as np # 引入 numpy 以支持更精确的数字类型处理
from src.logger import logger

def process_data(raw_data) -> pd.DataFrame:
    """
    统一数据预处理入口
    仅负责清洗与格式化，特征工程（指标计算）已剥离至 src/indicators/
    """
    logger.info("开始执行工业级数据清洗与标准化...")
    
    # 1. 核心清洗逻辑 (clean_and_format)
    df = clean_and_format(raw_data)
    
    if df.empty:
        logger.error("数据清洗失败，返回空集。")
        return pd.DataFrame()
        
    logger.info(f"数据清洗完成，有效数据行数: {len(df)}")
    return df


def clean_and_format(df: object) -> pd.DataFrame:
    """
    数据清洗与标准化引擎 (yfinance 字典解析适配版)
    首先解析 yfinance 模拟的 AlphaVantage 字典结构，转换为 DataFrame，
    然后执行列名标准化、强制数字类型检查、时间排序与基准收益率计算。
    """
    # ==================== 核心新加：字典到 DataFrame 的转换解析层 ====================
    # 检查输入数据源
    time_series_key = "Time Series (Daily)"
    
    # 情况 A：如果接收到的是字典（说明来自新 yfinance 引擎），先解析
    if isinstance(df, dict) and time_series_key in df:
        time_series_data = df[time_series_key]
        if not time_series_data:
            logger.warning(f"[清洗拦截] 股票数据为空，拒绝进一步处理。")
            return pd.DataFrame() # 返回空 DataFrame
            
        # 解析字典：K 线日期作为行索引（orient='index'）
        df_cleaned = pd.DataFrame.from_dict(time_series_data, orient='index')
        
    # 情况 B：如果输入早已是一个 DataFrame（例如来自旧本地账本），直接使用
    elif isinstance(df, pd.DataFrame):
        if df.empty:
            return df
        df_cleaned = df.copy()
        
    else:
        logger.warning(f"[清洗拦截] 数据源非预期格式或不可读取，跳过该股票。")
        return pd.DataFrame()
    # ==============================================================================
    
    # 3. 统一列名标准化：移除旧 AlphaVantage JSON 的 "1. ", "2. " 前缀，并统一小写
    # 此步骤确保特征计算模块能通过 ['open', 'high'] 等干净字符读取数据
    df_cleaned.columns = [str(col).split('. ')[1].lower() if '. ' in col else str(col).lower() for col in df_cleaned.columns]
    
    # 4. 健壮的时间索引清洗：强制转换为 datetime 格式并按时间正序排列
    df_cleaned.index = pd.to_datetime(df_cleaned.index)
    df_cleaned = df_cleaned.sort_index()
    
    # 同步升级：强制数字类型检查 (将 JSON 字符串转化为浮点数/整数)
    # JSON 字典转换出的 DataFrame 里，Open/High/Close 等价格默认都是 string。
    # 必须显式地把价格列强制转换为 float64 类型，把 volume 强制转换为 Int64，
    # 否则后方的特征计算和神经网络模型会因为啃到字符串而崩溃或逻辑错乱。
    price_cols = ['open', 'high', 'low', 'close']
    for col in price_cols:
        if col in df_cleaned.columns:
            # errors='coerce' 会把无法转换的值转为 NaN，避免崩溃
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

    if 'volume' in df_cleaned.columns:
        df_cleaned['volume'] = pd.to_numeric(df_cleaned['volume'], errors='coerce').astype('Int64')

    # 5. 清理 NaN 值：删除在类型检查和解析中产生的坏样本
    df_cleaned = df_cleaned.dropna()

    # 6. 预计算基准收益率（大盘买入持有）的每日收益率与累计收益率，供审计对比
    if 'close' in df_cleaned.columns and not df_cleaned.empty:
        df_cleaned['market_return'] = df_cleaned['close'].pct_change().fillna(0)
        df_cleaned['cum_market_return'] = (1 + df_cleaned['market_return']).cumprod() - 1
        
    return df_cleaned


def save_to_csv(df: pd.DataFrame, symbol: str, output_dir: str = "data"):
    """
    工业级双轨制数据落盘引擎 (CSV+JSON)
    不仅保存全量交易账本 CSV，同时对核心量化指标进行原子化抽取，保存为高频轻量 JSON 快照
    """
    if df.empty:
        logger.warning(f"[落盘引擎] {symbol} 数据流为空，拒绝写入磁盘。")
        return

    #自动化目录矩阵创建
    os.makedirs(output_dir, exist_ok=True)
    
    #轨道 A：全量级历史对账单落盘 (CSV) - index=True 完整保留时间戳
    csv_path = os.path.join(output_dir, f"{symbol}_backtest_ledger.csv")
    df.to_csv(csv_path, index=True, encoding='utf-8-sig') # 确保 Excel 打开中文不乱码
    
    #轨道 B：高价值绩效快照提炼落盘 (JSON)
    try:
        summary_path = os.path.join(output_dir, f"{symbol}_performance_summary.json")
        
        # 提炼全局核心指标，形成原子化的结构化 JSON 数据
        total_days = len(df)
        final_returns = (df['total_value'].iloc[-1] / df['total_value'].iloc[0]) - 1 if 'total_value' in df.columns else 0.0
        
        metrics_snapshot = {
            "metadata": {
                "symbol": symbol.upper(),
                "total_trading_days": int(total_days),
                "data_engine_version": "yfinance_neural_v2",
                "creation_time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "performance_metrics": {
                "strategy_total_return_pct": float(final_returns * 100.0),
                "final_portfolio_value_usd": float(df['total_value'].iloc[-1]) if 'total_value' in df.columns else 100000.0,
                "market_buy_and_hold_return_pct": float(df['cum_market_return'].iloc[-1] * 100.0) if 'cum_market_return' in df.columns else 0.0
            }
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_snapshot, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        logger.warning(f"[落盘引擎] 提炼 JSON 绩效快照时发生非致命异常: {e}")

