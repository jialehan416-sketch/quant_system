import requests
from typing import Optional
def fetch_daily_data(symbol: str, api_key: str) -> Optional[dict]:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",  #日频历史行情
        "symbol": symbol,  #函数外部传进来的股票代码赋值给API参数symbol
        "outputsize": "full",  #获取完整数据
        "apikey": api_key  #函数外部传进来的API密钥赋值给API参数apikey
    }
    print(f"正在获取{symbol}的日频历史行情数据...")
    try: #使用requests库的get方法发送HTTP GET请求，获取API返回的数据，并设置请求超时时间为15秒
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"请求{symbol}失败,HTTPS状态: {response.status_code}")
            return None
        
        data = response.json()  #将API返回的JSON数据解析为Python字典

        #检查API返回的数据中是否包含"Note"或"Information"字段，这些字段通常表示请求被限流或其他问题
        if "Note" in data or "Information" in data:
            limit_msg = data.get("Note", data.get("Information", ""))
            print (f"[触发限流]{symbol} 请求被拦截：{limit_msg}")
            return None
        
        #检查API返回的数据中是否包含"Error Message"字段，这通常表示请求的股票代码无效或API请求错误
        if "Error Message" in data:
            print(f"[API报错] 股票代码 {symbol} 无效或API请求错误：{data['Error Message']}")
            return None 
        
        #检查API返回的数据中是否包含"Time Series (Daily)"字段，这个字段应该包含日频历史行情数据，如果缺失则说明返回的数据结构不符合预期
        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            print(f"[数据异常] {symbol} 返回的数据结构不符合预期。")
            return None
        
        print(f"成功获取{symbol}的原始数据。")
        return data[time_series_key]  #返回API返回的数据中"Time Series (Daily)"字段的值，即日频历史行情数据
    
    except requests.exceptions.RequestException as e:  #捕获requests库可能抛出的异常，如连接错误、超时等，并打印错误信息
        print(f"请求{symbol}时发生错误：{e}") #返回None表示数据获取失败
        return None

#本地检测
if __name__ == "__main__":
    Test_API_KEY = "demo"
    Test_Symbol = "IBM"
    print("开始测试数据获取模块")
    #调用fetch_daily_data函数获取测试股票代码的日频历史行情数据，并将结果存储在变量result中
    result = fetch_daily_data(Test_Symbol, Test_API_KEY)

    if result:
        print(f"\n预览获取到的前3条数据：")
        dates = list(result.keys())[:3] #获取结果字典中的前3个日期键，并将它们存储在变量dates中
        for date in dates: #遍历前3个日期键，并打印每个日期及其对应的日频历史行情数据
            print(f"{date}: {result[date]}") #打印每个日期及其对应的日频历史行情数据
    else:
        print("数据获取失败，无法预览。")