import time   #api 07UVHKLQ5Z1HFA2F
import os
from src.data_fetcher import fetch_daily_data
from src.data_processor import clean_and_format, save_to_csv
from src.data_strategy import calculate_indicators, generate_signals
from src.data_backtester import run_backtest, print_performance_summary
from src.data_visualizer import plot_equity_curve 
DATA_DIR = "data"
REPORT_DIR = "reports"
def get_user_config():
    #交互方式获取用户输入的API Key和股票代码，并进行基本的输入验证和清洗
    print("\n" + "=" * 50)
    print("⚙️  量化系统初始化配置")
    print("=" * 50)
    
    api_input = input("请输入你的 AlphaVantage API Key (直接回车默认使用 'demo'): ").strip()
    # 如果用户没输入直接敲了回车，就默认用 demo
    if not api_input:
        api_key = "demo"
        print("   -> 已自动切换为测试密钥 'demo' (注意: demo 只能查 IBM)")
    else:
        api_key = api_input
        
    #交互式获取股票代码
    stock_input = input("请输入想要下载的美股代码 (多个代码用英文逗号分隔, 例如 AAPL,MSFT,TSLA): ").strip()
    
    if not stock_input:
        # 如果用户没输入直接敲了回车
        stock_pool = ["IBM"] if api_key == "demo" else ["AAPL"]
        print(f"   -> 未检测到输入，默认加载股票池: {stock_pool}")
    else:
        # 核心清洗魔法：按逗号分割 -> 去除首尾空格 -> 强制转大写 -> 过滤空字符串
        stock_pool = [s.strip().upper() for s in stock_input.split(",") if s.strip()]
        
    print("=" * 50 + "\n")
    return api_key, stock_pool

def main():
    API_KEY, STOCK_POOL = get_user_config()
    print("启动量化系统第二阶段：数据获取、指标计算与信号生成一体化流水线")
    print(f"目标数据存放目录: {os.path.abspath(DATA_DIR)}")
    print("-" * 50)
    total_stocks = len(STOCK_POOL)
    for index, symbol in enumerate(STOCK_POOL):
        print(f"\n[{index + 1}/{total_stocks}] 开始处理股票: {symbol}")
        raw_data = fetch_daily_data(symbol, API_KEY)
        if raw_data is None:
            print(f"股票 {symbol} 数据获取失败，跳过...")
            continue
        #清洗并对齐格式
        df_cleaned = clean_and_format(raw_data)
        
        #计算技术指标 (5日与10日均线)
        print (f"正在计算 {symbol} 的 5日 与 10日 移动平均线...") #计算双均线技术指标
        df_with_indicators = calculate_indicators(df_cleaned, short_window=5, long_window=10)

        print(f"正在捕捉 {symbol} 的金叉死叉状态切换，生成交易信号...")
        df_with_signals = generate_signals(df_with_indicators) #基于指标，一阶差分自发生成交易信号

        print(f"正在启动向量化回测引擎，清算 {symbol} 历史账本...")
        df_backtested = run_backtest(df_with_signals, initial_capital=100000.0)

        #控制台战报输出
        print_performance_summary(df_backtested)

        #全量数字资产矩阵落盘 (CSV 账本)
        save_to_csv(df_backtested, symbol, output_dir=DATA_DIR)

        # 绘制并保存资产曲线图
        plot_equity_curve(df_backtested, symbol, output_dir=REPORT_DIR)

        if index < total_stocks - 1:
            wait_seconds = 15
            print(f"触发 API 保护机制，强制休眠 {wait_seconds} 秒以防止限流封禁...")
            time.sleep(wait_seconds)
    print("-" * 50)
    print("【全线大捷】所有目标股票回测清算完毕！请前往 data/ 文件夹查看最终资产曲线账本")

if __name__ == "__main__":
    main()
