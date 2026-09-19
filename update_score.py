import json
import datetime
import os
import random
import requests
import yfinance as yf
import feedparser

# ---------------------------------------------------------
# 1. OFFICIAL SOURCES (70% Weight) - RECALIBRATED SENSITIVITY
# ---------------------------------------------------------
def get_official_score():
    try:
        # VIX: A VIX of 15 is normal. 20+ is elevated.
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[0]
        vix_score = min(40 + ((vix - 12) * 2.5), 100) 
        
        # Oil: Highly sensitive to Middle East / Houthi / Russian supply issues
        oil = yf.Ticker("CL=F").history(period="5d")
        oil_trend = (oil['Close'].iloc[-1] - oil['Close'].iloc[0]) / oil['Close'].iloc[0]
        oil_score = 55 + (oil_trend * 800) # Amplified sensitivity to small spikes
        
        # Gold: Safe haven asset. Already historically high.
        gold = yf.Ticker("GC=F").history(period="5d")
        gold_trend = (gold['Close'].iloc[-1] - gold['Close'].iloc[0]) / gold['Close'].iloc[0]
        gold_score = 65 + (gold_trend * 800) # Higher baseline because gold is currently surging
        
        score = (vix_score * 0.4) + (oil_score * 0.3) + (gold_score * 0.3)
        return max(0, min(100, score))
    except Exception as e:
        return 60 # Higher default baseline for current global climate

# ---------------------------------------------------------
# 2. UNOFFICIAL SOURCES (30% Weight) - EXPANDED KEYWORDS
# ---------------------------------------------------------
def get_unofficial_score():
    # Expanded to catch current European, Ukrainian, and Middle Eastern escalations
    keywords = [
        'war', 'escalation', 'hybrid', 'strike', 'missile', 'alerts', 
        'idf', 'houthis', 'lebanon', 'putin', 'nato', 'nuclear', 'crisis', 'draft'
    ]
    threat_count = 0
    try:
        urls = [
            'https://www.reddit.com/r/worldnews/top/.rss?t=day',
            'https://www.reddit.com/r/geopolitics/top/.rss?t=day'
        ]
        headers = {'User-Agent': 'Mozilla/5.0'}
        for url in urls:
            response = requests.get(url, headers=headers)
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                text = (entry.title).lower()
                if any(word in text for word in keywords):
                    threat_count += 1
                    
        # Every hit adds 3 points to a baseline of 50
        score = min(50 + (threat_count * 3), 100)
        return score
    except Exception as e:
        return 60

# ---------------------------------------------------------
# 3. HEAT MAP DATA (Added explicit regional targets)
# ---------------------------------------------------------
def get_map_data():
    return {
        # 3: Ongoing Direct Conflict
        "RU": 3, "UA": 3, "IL": 3, "LB": 3, "PS": 3, "SY": 3, "YE": 3, "SD": 3, "MM": 3,
        # 2: High Threat / Targeted / Proxy involvement
        "TW": 2, "IR": 2, "KP": 2, "KR": 2, "SA": 2, "PK": 2, "BY": 2,
        # 1: Potential Conflict / Tense Borders / Energy Crisis Impacts
        "CN": 1, "PH": 1, "RS": 1, "VE": 1, "GY": 1, "IN": 1, "PL": 1, "DE": 1
    }

# ---------------------------------------------------------
# 4. CORE ALGORITHM & DATA EXPORT
# ---------------------------------------------------------
def main():
    official_score = get_official_score()
    unofficial_score = get_unofficial_score()
    final_score = (official_score * 0.7) + (unofficial_score * 0.3)
    
    today_str = datetime.datetime.utcnow().strftime('%m-%d')
    history = []
    
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                history = json.load(f).get('history', [])
        except:
            pass
            
    # Generate smoothed recent mock history ending at our new recalibrated baseline
    if not history or len(history) < 2:
        base_score = final_score - random.uniform(1, 4)
        for i in range(30, 0, -1):
            past_date = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime('%m-%d')
            mock_score = base_score + random.uniform(-2, 2.5)
            base_score = mock_score
            history.append({"date": past_date, "score": round(max(0, min(100, mock_score)), 1)})

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
        "status": "CRITICAL" if final_score > 75 else "ELEVATED" if final_score > 55 else "STABLE",
        "history": history,
        "map_data": get_map_data()
    }
    
    with open('data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=4)

if __name__ == "__main__":
    main()
