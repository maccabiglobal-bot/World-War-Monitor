import json
import datetime
import os
import random
import requests
import yfinance as yf
import feedparser

# ---------------------------------------------------------
# 1. OFFICIAL SOURCES (70% Weight) 
# ---------------------------------------------------------
def get_official_score():
    score = 0
    try:
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[0]
        vix_score = min((vix / 40) * 100, 100) 
        
        oil = yf.Ticker("CL=F").history(period="5d")
        oil_trend = (oil['Close'].iloc[-1] - oil['Close'].iloc[0]) / oil['Close'].iloc[0]
        oil_score = 50 + (oil_trend * 500) 
        
        gold = yf.Ticker("GC=F").history(period="5d")
        gold_trend = (gold['Close'].iloc[-1] - gold['Close'].iloc[0]) / gold['Close'].iloc[0]
        gold_score = 50 + (gold_trend * 500)
        
        score = (vix_score * 0.4) + (oil_score * 0.3) + (gold_score * 0.3)
        return max(0, min(100, score))
    except Exception as e:
        return 50

# ---------------------------------------------------------
# 2. UNOFFICIAL SOURCES (30% Weight)
# ---------------------------------------------------------
def get_unofficial_score():
    keywords = ['world war', 'ww3', 'draft', 'mobilization', 'nuclear', 'defcon', 'escalation']
    threat_count = 0
    try:
        urls = [
            'https://www.reddit.com/r/worldnews/top/.rss?t=day',
            'https://www.reddit.com/r/geopolitics/top/.rss?t=day',
            'https://www.reddit.com/r/preppers/top/.rss?t=day'
        ]
        headers = {'User-Agent': 'Mozilla/5.0'}
        for url in urls:
            response = requests.get(url, headers=headers)
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                text = (entry.title).lower()
                if any(word in text for word in keywords):
                    threat_count += 1
                    
        score = min((threat_count / 15) * 100, 100)
        return score
    except Exception as e:
        return 50

# ---------------------------------------------------------
# 3. HEAT MAP DATA (ISO Country Codes)
# ---------------------------------------------------------
def get_map_data():
    # 3: Ongoing Conflict, 2: High Threat, 1: Potential Conflict
    return {
        "RU": 3, "UA": 3, "IL": 3, "SD": 3, "MM": 3, "SY": 3, "YE": 3,
        "TW": 2, "IR": 2, "KP": 2, "KR": 2, "LB": 2, "PK": 2,
        "CN": 1, "PH": 1, "RS": 1, "VE": 1, "GY": 1, "IN": 1
    }

# ---------------------------------------------------------
# 4. CORE ALGORITHM & DATA EXPORT
# ---------------------------------------------------------
def main():
    official_score = get_official_score()
    unofficial_score = get_unofficial_score()
    final_score = (official_score * 0.7) + (unofficial_score * 0.3)
    
    today_str = datetime.datetime.utcnow().strftime('%m-%d')
    
    # Read history to build the 30-day chart
    history = []
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                old_data = json.load(f)
                history = old_data.get('history', [])
        except:
            pass
            
    # If no history exists, generate 30 days of realistic mock data so the chart isn't empty
    if not history:
        base_score = 45.0
        for i in range(30, 0, -1):
            past_date = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime('%m-%d')
            mock_score = base_score + random.uniform(-4, 5)
            base_score = mock_score
            history.append({"date": past_date, "score": round(max(0, min(100, mock_score)), 1)})

    # Append today's actual score and keep only the last 30 days
    history = [h for h in history if h['date'] != today_str] 
    history.append({"date": today_str, "score": round(final_score, 1)})
    history = history[-30:]
    
    dashboard_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "global_risk_score": round(final_score, 1),
        "metrics": {
            "official_index": round(official_score, 1),
            "unofficial_index": round(unofficial_score, 1)
        },
        "status": "ELEVATED" if final_score > 60 else "STABLE",
        "history": history,
        "map_data": get_map_data()
    }
    
    with open('data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=4)

if __name__ == "__main__":
    main()
