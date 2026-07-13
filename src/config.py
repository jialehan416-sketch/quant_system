# src/config.py
import os
import yaml
from src.logger import logger

# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

def load_global_config() -> dict:
    """
    工业级配置加载引擎
    支持物理文件读取，若文件丢失则自动启动防御性默认配置，确保生产环境不崩溃
    """
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                logger.info("成功从物理配置文件 (config.yaml) 中加载系统运行参数。")
                return config
        except Exception as e:
            logger.error(f"配置文件解析失败: {e}。将启用防御性内建配置。")
            
    # 防御性内建兜底配置（防止漏掉文件导致程序直接闪退）
    logger.warning("未找到物理 config.yaml，当前正在使用内存兜底配置运行！")
    return {
        "DATA_DIR": "data",
        "REPORT_DIR": "reports",
        "STRATEGY_PARAMS": {
            "short_window": 5, "long_window": 10, "trend_window": 60,
            "rsi_window": 14, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
            "bb_window": 20, "bb_std": 2.0, "kdj_window": 9, "atr_window": 14
        },
        "ADAPTIVE_PARAMS": {"rolling_window": 40, "top_q": 0.82, "bottom_q": 0.18},
        "BACKTEST_PARAMS": {"initial_capital": 100000.0, "commission": 0.0003, "slippage": 0.0005},
        "DEFAULT_STOCKS": ["TSLA", "AAPL", "NVDA", "MSFT"]
    }

# 全局唯一配置单例，供全系统所有模块直接 import 调用
GLOBAL_CONFIG = load_global_config()