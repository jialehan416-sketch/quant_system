import time
import os
import torch  # 用于检测硬件加速状态
import matplotlib  # 用于全局中文字体环境修复
from src.logger import logger

# 1. 核心重构：引入外部解耦后的全局系统配置中心
from src.config import GLOBAL_CONFIG
# 【修复点 1】：导入全新的指标插件自动化工厂
from src.indicators import apply_all_indicators 

# 导入你现有的 5 大核心模块函数
from src.data_fetcher import fetch_daily_data
from src.data_processor import clean_and_format, save_to_csv
from src.data_strategy import generate_signals
from src.data_backtester import run_backtest, print_performance_summary
from src.data_visualizer import plot_equity_curve

# 彻底解决回测绘图时可能出现的 CJK UNIFIED IDEOGRAPH / 豆腐块乱码警告
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False


def get_user_system_config(config: dict):
    logger.info("\n" + "=" * 50)
    logger.info("量化系统初始化配置 (1/3)")
    logger.info("[数据引擎]: yfinance 雅虎财经免密高速接入")
    logger.info("=" * 50)
    
    stock_input = input("请输入想要下载的美股代码 (多个用英文逗号分隔, 例如 TSLA,AAPL 直接回车使用默认池): ").strip()
    if not stock_input:
        stock_pool = config["DEFAULT_STOCKS"]
        logger.info(f"  -> 未检测到输入, 默认加载核心监控池: {stock_pool}")
    else:
        stock_pool = [s.strip().upper() for s in stock_input.split(",") if s.strip()]
    return stock_pool


def get_user_strategy_config(config: dict):
    logger.info("\n" + "=" * 50)
    logger.info("底层技术指标参数微调 (2/3)")
    logger.info(" (这些指标将转化为环境状态，供 DQN 强化学习智能体观察)")
    logger.info("=" * 50)
    dp = config["STRATEGY_PARAMS"]
    
    def safe_input(prompt_text, default_val):
        user_val = input(prompt_text).strip()
        if not user_val: 
            return default_val
        try: 
            return int(user_val)
        except ValueError: 
            return default_val
        
    strategy_params = {
        "short_window": safe_input(f"1. 短期快线 short_window (默认 {dp['short_window']}): ", dp['short_window']),
        "long_window": safe_input(f"2. 长期慢线 long_window (默认 {dp['long_window']}): ", dp['long_window']),
        "trend_window": safe_input(f"3. 牛熊线 trend_window (默认 {dp['trend_window']}): ", dp['trend_window']),
        "rsi_window": safe_input(f"4. RSI动量窗口 rsi_window (默认 {dp['rsi_window']}): ", dp['rsi_window']),
        "macd_fast": safe_input(f"5. MACD快线 macd_fast (默认 {dp['macd_fast']}): ", dp['macd_fast']),
        "macd_slow": dp['macd_slow'], 
        "macd_signal": dp['macd_signal'],
        "bb_window": safe_input(f"6. 布林带窗口 bb_window (默认 {dp['bb_window']}): ", dp['bb_window']),
        "bb_std": dp['bb_std'],
        "kdj_window": safe_input(f"7. KDJ探索窗口 kdj_window (默认 {dp['kdj_window']}): ", dp['kdj_window']),
        "atr_window": safe_input(f"8. ATR风控波幅 atr_window (默认 {dp['atr_window']}): ", dp['atr_window']),
    }
    return strategy_params


def get_user_factor_switches():
    logger.info("\n" + "=" * 50)
    logger.info("DQN 强化学习脑区特征输入选择面板 (3/3)")
    logger.info(" (输入 y 将特征喂给强化学习网络, 输入 n 剔除。直接回车默认全选)")
    logger.info("=" * 50)
    
    factors_metadata = [
        ('MA', '双均线比率特征 (MA_ratio, MA_trend)'),
        ('TREND', '大盘牛熊偏离特征 (TREND_ratio)'),
        ('RSI', 'RSI动量缩放特征 (F_RSI)'),
        ('MACD', 'MACD柱体相对强弱特征 (F_MACD)'),
        ('BB', '布林带波动轨道相对位置 (F_BB_pos)'),
        ('KDJ', 'KDJ变盘动能特征 (F_KDJ)'),
        ('ATR', 'ATR动态波动率风险特征 (F_ATR_ratio)')
    ]
    
    enabled_factors = {}
    for code, name in factors_metadata:
        choice = input(f" -> 允许智能体观察并学习 【{name}】? (y/n, 默认 y): ").strip().lower()
        enabled_factors[code] = False if choice == 'n' else True
        
    logger.info("=" * 50 + "\n")
    return enabled_factors


def main():
    # 检测硬件环境并给出友好提示
    device_name = "英伟达 GPU 加速 (CUDA)" if torch.cuda.is_available() else "中央处理器 (CPU)"
    
    # 引导用户完成交互式配置（直接传入解耦导入的 GLOBAL_CONFIG）
    STOCK_POOL = get_user_system_config(GLOBAL_CONFIG)
    strategy_params = get_user_strategy_config(GLOBAL_CONFIG)
    enabled_factors = get_user_factor_switches()
    
    # 将用户在终端交互微调的指标参数同步更新到全局配置单例中，确保后续插件能动态感知
    GLOBAL_CONFIG["STRATEGY_PARAMS"].update(strategy_params)
    
    # 解包核心回测控制参数
    initial_capital = GLOBAL_CONFIG["BACKTEST_PARAMS"]["initial_capital"]
    commission = GLOBAL_CONFIG["BACKTEST_PARAMS"]["commission"]
    slippage = GLOBAL_CONFIG["BACKTEST_PARAMS"]["slippage"]
    
    data_dir = GLOBAL_CONFIG["DATA_DIR"]
    report_dir = GLOBAL_CONFIG["REPORT_DIR"]
    
    # 创建必要的落盘目录
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    active_features = [k for k, v in enabled_factors.items() if v]
    
    logger.info("\n" + "#" * 60)
    logger.info(f"Deep Reinforcement Learning (DRL) 量化引擎启动...")
    logger.info(f" [运行硬件]: {device_name}")
    logger.info(f" [观察空间]: {active_features} (状态维度: {len(active_features)})")
    logger.info(f" [决策核心]: DQN (Deep Q-Network) 智能操盘手连续试错进化")
    logger.info(f" [记忆机制]: 自动读写硬盘文件 'quant_brain_dqn.pth' 传承跨资产经验")
    logger.info("#" * 60 + "\n")
    
    total_stocks = len(STOCK_POOL)
    successful_count = 0
    
    for index, symbol in enumerate(STOCK_POOL):
        logger.info(f"\n[{index + 1}/{total_stocks}]正在将智能体投入实战环境: {symbol}")
        
        # 1. 抓取与清洗
        raw_data = fetch_daily_data(symbol)
        if raw_data is None:
            logger.warning(f"[数据断档] 股票 {symbol} 获取失败, 自动跳过。")
            continue
            
        df_cleaned = clean_and_format(raw_data)
        if df_cleaned.empty:
            logger.warning(f"[清洗拦截] 股票 {symbol} 转换后为空, 自动跳过。")
            continue
            
        # 【修复点 2】：不再错误地调用 generate_signals，而是通过工厂一键挂载解耦的技术特征
        df_with_indicators = apply_all_indicators(df_cleaned)
        
        # 3. 激活强化学习：调用融合了 DQN 与经验落盘机制的信号生成器
        df_with_signals = generate_signals(
            df_with_indicators, 
            enabled_factors=enabled_factors,
            rolling_window=GLOBAL_CONFIG["ADAPTIVE_PARAMS"]["rolling_window"],
            top_q=GLOBAL_CONFIG["ADAPTIVE_PARAMS"]["top_q"],
            bottom_q=GLOBAL_CONFIG["ADAPTIVE_PARAMS"]["bottom_q"]
        )
        
        # 4. 运行包含真实交易摩擦成本的回测结算
        df_backtested = run_backtest(
            df_with_signals, 
            initial_capital=initial_capital, 
            commission=commission, 
            slippage=slippage
        )
        
        # 5. 终端打印审计看板
        print_performance_summary(df_backtested, slippage=slippage)
        
        # 6. 数据与资产曲线双轨落盘保存
        save_to_csv(df_backtested, symbol, output_dir=data_dir)
        plot_equity_curve(df_backtested, symbol, output_dir=report_dir)
        
        logger.info(f"数据落盘成功 | 全量级交易账本: {data_dir}/{symbol}_backtest_ledger.csv")
        logger.info(f"净值渲染成功 | 纯净版回测全景: {report_dir}/{symbol}_equity_curve.png")
        successful_count += 1
        
        # 频率控制，防止被数据源高频风控
        if index < total_stocks - 1:
            time.sleep(1)
            
    logger.info("\n" + "=" * 60)
    logger.info(f"【深度强化学习演练成功】所有监控资产实战训练已全部完成！")
    logger.info(f"成功完成智能决策与回测的股票总数: {successful_count}/{total_stocks}")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    main()