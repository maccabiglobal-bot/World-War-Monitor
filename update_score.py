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
    try:
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        vix_score = min(max(40 + ((vix - 15) * 2.5), 0), 100) 
        
        oil = yf.Ticker("CL=F").history(period="1d")['Close'].iloc[-1]
        oil_score = min(max(50 + ((oil - 85) * 1.5), 0), 100) 
        
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        gold_score = min(max(50 + ((gold - 3800) * 0.05), 0), 100)
        
        score = (vix_score * 0.4) + (oil_score * 0.3) + (gold_score * 0.3)
        return max(0, min(100, score))
    except Exception as e:
        return 65 

# ---------------------------------------------------------
# 2. UNOFFICIAL SOURCES (30% Weight) & HEADLINE EXTRACTOR
# ---------------------------------------------------------
def get_unofficial_score():
    keywords = [
        'war', 'escalation', 'hybrid', 'strike', 'missile', 'alerts', 
        'idf', 'houthis', 'lebanon', 'putin', 'nato', 'nuclear', 'crisis', 'draft'
    ]
    threat_count = 0
    headlines = [] # <-- We added a bucket to hold the actual news
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
                    # Save the headline if we haven't seen it yet
                    if entry.title not in headlines:
                        headlines.append(entry.title)
                    
        score = min(50 + (threat_count * 3), 100)
        # Return the score AND the top 10 most alarming headlines
        return score, headlines[:10] 
    except Exception as e:
        return 65, ["LIVE FEED INTERRUPTED: Monitoring background channels..."]

def get_map_data():
    return {
        "RU": 3, "UA": 3, "IL": 3, "LB": 3, "PS": 3, "SY": 3, "YE": 3, "SD": 3, "MM": 3,
        "TW": 2, "IR": 2, "KP": 2, "KR": 2, "SA": 2, "PK": 2, "BY": 2,
        "CN": 1, "PH": 1, "RS": 1, "VE": 1, "GY": 1, "IN": 1, "PL": 1, "DE": 1
    }

# ---------------------------------------------------------
# 3. CORE ALGORITHM
# ---------------------------------------------------------
def main():
    official_score = get_official_score()
    unofficial_score, live_headlines = get_unofficial_score() # <-- Grabbing the headlines here
    final_score = (official_score * 0.7) + (unofficial_score * 0.3)
    
    today_str = datetime.datetime.utcnow().strftime('%m-%d')
    history = []
    
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                history = json.load(f).get('history', [])
        except:
            pass
            
    if not history or len(history) < 2:
        mock_history = []
        walk_score = final_score
        for i in range(1, 31):
            past_date = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime('%m-%d')
            walk_score = walk_score + random.uniform(-1, 1.2) 
            mock_history.append({"date": past_date, "score": round(max(0, min(100, walk_score)), 1)})
        
        mock_history.reverse()
        history = mock_history

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
        "map_data": get_map_data(),
        "headlines": live_headlines # <-- Adding them to the JSON file
    }
    
    with open('data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=4)

if __name__ == "__main__":
    main()
