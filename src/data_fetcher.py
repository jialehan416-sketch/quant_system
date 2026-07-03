import requests

def fetch_daily_data(symbol: str, api_key: str) -> dict:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact"  # compact 返回近 100 条数据，full 返回 20 年数据
    }
    try:
        print(f"   [API 请求] 正在向 AlphaVantage 请求 {symbol} 的日线数据...")
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        # 错误卡口
        if "Error Message" in data:
            print(f"API 报错: 请检查股票代码 [{symbol}] 是否正确。")
            return None
        if "Note" in data:
            print("触发 AlphaVantage 频次限制 (免费 Key 每分钟 5 次)，请稍后再试或换用付费 Key。")
            return None
        if "Time Series (Daily)" not in data:
            print("未在返回结果中找到时间序列数据，可能 API Key 无效。")
            return None
            
        return data
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
        return None