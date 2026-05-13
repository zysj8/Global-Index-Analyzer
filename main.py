import pandas as pd
import yfinance as yf
import akshare as ak
import json
from datetime import datetime

# 核心配置：明确区分 source 以确保数据准确
INDEX_CONFIG = {
    "SPX": {"name": "标普500", "weight": 0.32, "ticker": "^GSPC", "source": "yf"},
    "NDX": {"name": "纳斯达克100", "weight": 0.32, "ticker": "^NDX", "source": "yf"},
    "N225": {"name": "日经225", "weight": 0.06, "ticker": "^N225", "source": "yf"},
    "FTSE": {"name": "英国富时100", "weight": 0.06, "ticker": "^FTSE", "source": "yf"},
    "FCHI": {"name": "法国CAC40", "weight": 0.04, "ticker": "^FCHI", "source": "yf"},
    "DAX": {"name": "德国DAX", "weight": 0.04, "ticker": "^GDAXI", "source": "yf"},
    "CSI300": {"name": "沪深300", "weight": 0.05, "symbol": "sh000300", "source": "ak_pe"},
    "CSI500": {"name": "中证500", "weight": 0.05, "symbol": "sh000905", "source": "ak_pe"},
    "HSI": {"name": "恒生指数", "weight": 0.03, "symbol": "hkHSI", "source": "ak_hk"},
    "HSTECH": {"name": "恒生科技", "weight": 0.03, "symbol": "hkHSTECH", "source": "ak_hk"}
}

def get_valuation_signal(percentile):
    """根据估值百分位计算梯度"""
    p = float(percentile)
    if p < 0.2: return 1.0
    elif p < 0.5: return 0.7
    elif p < 0.8: return 0.4
    else: return 0.15

def main():
    results = []
    print("开始执行全球组合分析...")
    
    for key, info in INDEX_CONFIG.items():
        try:
            method = "价格分位"
            pct = 0.0
            
            # 分源处理数据
            if info['source'] == "ak_pe":
                # A股抓取 PE (市盈率)
                df = ak.stock_a_indicator_lg(symbol=info['symbol'])
                curr = float(df['pe'].iloc[-1])
                hist = df['pe'].tail(2520).astype(float)
                pct = (hist < curr).mean()
                method = "PE分位"
            elif info['source'] == "ak_hk":
                # 港股抓取历史行情计算
                df = ak.stock_hk_index_daily_sina(symbol=info['symbol'])
                curr = float(df['close'].iloc[-1])
                hist = df['close'].tail(1250).astype(float)
                pct = (curr - hist.min()) / (hist.max() - hist.min())
            else:
                # 国际指数抓取 3 年价格区间
                data = yf.Ticker(info['ticker'])
                hist = data.history(period="3y")['Close'].dropna()
                curr = float(hist.iloc[-1])
                pct = (curr - hist.min()) / (hist.max() - hist.min())

            signal = get_valuation_signal(pct)
            
            # 解决 NaN 问题的关键：确保所有数值在写入前已转换为字符串或清晰的数字
            results.append({
                "index": info['name'],
                "method": method,
                "percentile": f"{round(float(pct) * 100, 2)}%",
                "target_weight": f"{int(float(info['weight']) * 100)}%",
                "suggested_pos": f"{round(signal * 100, 1)}%"
            })
        except Exception as e:
            print(f"处理 {info['name']} 时出错: {e}")
            # 即使报错也添加一个占位，防止网页显示缺失
            results.append({
                "index": info['name'],
                "method": "获取失败",
                "percentile": "0%",
                "target_weight": f"{int(float(info['weight']) * 100)}%",
                "suggested_pos": "15.0%"
            })

    # 输出 JSON
    report = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results
    }
    with open("valuation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)
    print("分析报告已生成。")

if __name__ == "__main__":
    main()
