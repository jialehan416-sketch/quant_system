import pandas as pd
import yfinance as yf
from src.logger import logger

def fetch_daily_data(symbol: str, api_key: str = None) -> dict:
    """
    工业级平替：换用 yfinance 彻底解开数据长度封印
    为了不破坏原有的 clean_and_format 管道，我们直接将 yfinance 的数据
    逆向打包成原本 AlphaVantage 的标准 JSON 字典格式！
    """
    logger.info(f"[yfinance 引擎] 正在跨洋拉取 {symbol} 过去 5 年的完整历史序列...")
    try:
        # 下载过去 5 年的完整日线
        df = yf.download(symbol, period="5y", progress=False)
        if df.empty:
            logger.warning(f"[yfinance] 未能获取到 {symbol} 的数据，请检查代码是否输入正确。")
            return None
            
        df = df.reset_index()
        
        # 兼容 2026 最新版 yfinance 的多级索引（MultiIndex）处理
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        df.columns = [col.lower() for col in df.columns]
        
        # 逆向构造 AlphaVantage 的经典字典字典结构
        time_series = {}
        for _, row in df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            time_series[date_str] = {
                "1. open": str(row['open']),
                "2. high": str(row['high']),
                "3. low": str(row['low']),
                "4. close": str(row['close']),
                "5. volume": str(row['volume'])
            }
            
        custom_json = {
            "Meta Data": {"2. Symbol": symbol.upper()},
            "Time Series (Daily)": time_series
        }
        return custom_json
        
    except Exception as e:
        logger.error(f"[yfinance 引擎] 致命拉取异常: {e}")
        return None
    
import os
from dotenv import load_dotenv
from src.logger import logger

# 1. 确保在读取前加载
load_dotenv()

# 2. 安全读取：如果读取不到，给一个默认空字符串，或者抛出更有意义的警告
api_key = os.getenv("DATA_API_KEY") 

if api_key:
    logger.info(f"成功加载密钥: {api_key[:5]}****")
else:
    # 这里我们使用 WARNING，而不是直接让程序崩溃
    logger.warning("未检测到 DATA_API_KEY，系统将进入无 API 密钥模式")
    api_key = "" # 赋予一个默认值，防止后续切片报错