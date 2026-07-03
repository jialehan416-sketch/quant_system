import time   #api 07UVHKLQ5Z1HFA2F
import os
from src.data_fetcher import fetch_daily_data
from src.data_processor import clean_and_format, save_to_csv
from src.data_strategy import calculate_indicators, generate_signals
from src.data_backtester import run_backtest, print_performance_summary
from src.data_visualizer import plot_equity_curve 

GLOBAL_CONFIG = {
    "DATA_DIR": "data",
    "REPORT_DIR": "reports",
    "STRATEGY_PARAMS": {
        "short_window": 5, "long_window": 10, "trend_window": 60, "rsi_window": 14,
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "bb_window": 20, "bb_std": 2.0,
        "kdj_window": 9, "atr_window": 14
    },
    "BACKTEST_PARAMS": { "initial_capital": 100000.0 },
    "API_PROTECTION": { "wait_seconds": 15, "default_key": "demo" },
    "DEFAULT_STOCKS": { "demo_pool": ["IBM"], "live_pool": ["AAPL"] }
}

def get_user_system_config(config: dict):
    print("\n" + "=" * 50)
    print("量化系统初始化配置 (1/3)")
    print("=" * 50)
    default_key = config["API_PROTECTION"]["default_key"]
    api_input = input(f"请输入你的 AlphaVantage API Key (直接回车默认使用 '{default_key}'): ").strip()
    api_key = api_input if api_input else default_key
    
    stock_input = input("请输入想要下载的美股代码 (多个代码用英文逗号分隔, 例如 AAPL,MSFT,TSLA): ").strip()
    if not stock_input:
        stock_pool = config["DEFAULT_STOCKS"]["demo_pool"] if api_key == default_key else config["DEFAULT_STOCKS"]["live_pool"]
        print(f"   -> 未检测到输入，默认加载股票池: {stock_pool}")
    else:
        stock_pool = [s.strip().upper() for s in stock_input.split(",") if s.strip()]
    return api_key, stock_pool

def get_user_strategy_config(config: dict):
    print("\n" + "=" * 50)
    print("策略因子参数数值微调 (2/3)")
    print("=" * 50)
    dp = config["STRATEGY_PARAMS"]
    
    def safe_input(prompt_text, default_val):
        user_val = input(prompt_text).strip()
        if not user_val: return default_val
        try: return int(user_val)
        except ValueError: return default_val

    short_window = safe_input(f"1. 短期快线 short_window (默认 {dp['short_window']}): ", dp['short_window'])
    long_window = safe_input(f"2. 长期慢线 long_window (默认 {dp['long_window']}): ", dp['long_window'])
    trend_window = safe_input(f"3. 牛熊线 trend_window (默认 {dp['trend_window']}): ", dp['trend_window'])
    rsi_window = safe_input(f"4. RSI动量窗口 rsi_window (默认 {dp['rsi_window']}): ", dp['rsi_window'])
    macd_fast = safe_input(f"5. MACD快线 macd_fast (默认 {dp['macd_fast']}): ", dp['macd_fast'])
    bb_window = safe_input(f"6. 布林带窗口 bb_window (默认 {dp['bb_window']}): ", dp['bb_window'])
    kdj_window = safe_input(f"7. KDJ探索窗口 kdj_window (默认 {dp['kdj_window']}): ", dp['kdj_window'])
    atr_window = safe_input(f"8. ATR风控波幅 atr_window (默认 {dp['atr_window']}): ", dp['atr_window'])
    
    strategy_params = {
        "short_window": short_window, "long_window": long_window, "trend_window": trend_window,
        "rsi_window": rsi_window, "macd_fast": macd_fast, "macd_slow": dp['macd_slow'],
        "macd_signal": dp['macd_signal'], "bb_window": bb_window, "bb_std": dp['bb_std'],
        "kdj_window": kdj_window, "atr_window": atr_window
    }
    return strategy_params

def get_user_factor_switches():
    """
    🌟 新增第三阶段交互：让用户掌控生死大权，自由勾选想激活的策略因子
    """
    print("\n" + "=" * 50)
    print("策略因子乐高积木拼装面板 (3/3)")
    print("(输入 y 开启，输入 n 关闭。直接回车默认全部开启)")
    print("=" * 50)
    
    factors_metadata = [
        ('MA', '双均线交叉 (快慢线金叉死叉交易)'),
        ('TREND', '趋势生命线 (过滤牛市开仓/跌破强制清仓)'),
        ('RSI', 'RSI动量强弱 (超买平仓防守/防高位追入)'),
        ('MACD', 'MACD柱体多头 (要求红柱动量爆发期才准买)'),
        ('BB', '布林带轨道边界 (防止突破上轨追高/跌破中轨撤退)'),
        ('KDJ', 'KDJ极速指标 (辅助短线变盘金叉共振)'),
        ('ATR', 'ATR追踪动态止损 (根据市场绝对波幅高位锁利)')
    ]
    
    enabled_factors = {}
    for code, name in factors_metadata:
        choice = input(f" -> 是否激活【{name}】? (y/n, 默认 y): ").strip().lower()
        enabled_factors[code] = False if choice == 'n' else True
        
    print("=" * 50 + "\n")
    return enabled_factors

def main():
    # 三步走纯净交互
    API_KEY, STOCK_POOL = get_user_system_config(GLOBAL_CONFIG)
    strategy_params = get_user_strategy_config(GLOBAL_CONFIG)
    enabled_factors = get_user_factor_switches()
    
    initial_capital = GLOBAL_CONFIG["BACKTEST_PARAMS"]["initial_capital"]
    data_dir = GLOBAL_CONFIG["DATA_DIR"]
    report_dir = GLOBAL_CONFIG["REPORT_DIR"]
    api_proto = GLOBAL_CONFIG["API_PROTECTION"]
    
    # 精美打印当前被激活的“多因子兵团”
    active_names = [k for k, v in enabled_factors.items() if v]
    print(f"量化引擎启动！当前核心战略兵团已就位: {active_names}")
    print("-" * 50)
    
    total_stocks = len(STOCK_POOL)
    for index, symbol in enumerate(STOCK_POOL):
        print(f"\n[{index + 1}/{total_stocks}] 开始处理股票: {symbol}")
        raw_data = fetch_daily_data(symbol, API_KEY)
        if raw_data is None: continue
            
        df_cleaned = clean_and_format(raw_data)
        if df_cleaned.empty: continue
            
        #数据流穿透
        df_with_indicators = calculate_indicators(df_cleaned, **strategy_params)
        #动态路由核心注入：传入用户亲手拼装的因子开关
        df_with_signals = generate_signals(df_with_indicators, enabled_factors=enabled_factors) 
        df_backtested = run_backtest(df_with_signals, initial_capital=initial_capital)

        print_performance_summary(df_backtested)
        save_to_csv(df_backtested, symbol, output_dir=data_dir)
        plot_equity_curve(df_backtested, symbol, output_dir=report_dir)

        if index < total_stocks - 1:
            time.sleep(api_proto["wait_seconds"])
            
    print("-" * 50)
    print(f"【全线大捷】拼装回测清算完毕！请前往 {data_dir}/ 查看结果。")

if __name__ == "__main__":
    main()