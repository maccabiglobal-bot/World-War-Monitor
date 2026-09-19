import json
import datetime
import requests
import yfinance as yf
import feedparser

# ---------------------------------------------------------
# 1. OFFICIAL SOURCES (70% Weight) - Macro & Geopolitical
# ---------------------------------------------------------
def get_official_score():
    score = 0
    try:
        # A. Volatility Index (VIX)
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[0]
        vix_score = min((vix / 40) * 100, 100) 
        
        # B. Crude Oil (CL=F)
        oil = yf.Ticker("CL=F").history(period="5d")
        oil_trend = (oil['Close'].iloc[-1] - oil['Close'].iloc[0]) / oil['Close'].iloc[0]
        oil_score = 50 + (oil_trend * 500) 
        
        # C. Gold (GC=F)
        gold = yf.Ticker("GC=F").history(period="5d")
        gold_trend = (gold['Close'].iloc[-1] - gold['Close'].iloc[0]) / gold['Close'].iloc[0]
        gold_score = 50 + (gold_trend * 500)
        
        score = (vix_score * 0.4) + (oil_score * 0.3) + (gold_score * 0.3)
        return max(0, min(100, score))
    except Exception as e:
        print(f"Error fetching official data: {e}")
        return 50

# ---------------------------------------------------------
# 2. UNOFFICIAL SOURCES (30% Weight) - OSINT & Social Sentiment
# ---------------------------------------------------------
def get_unofficial_score():
    keywords = ['world war', 'ww3', 'draft', 'mobilization', 'nuclear', 'defcon', 'escalation']
    threat_count = 0
    
    try:
        # Bypass API keys using Reddit's public RSS feeds
        urls = [
            'https://www.reddit.com/r/worldnews/top/.rss?t=day',
            'https://www.reddit.com/r/geopolitics/top/.rss?t=day',
            'https://www.reddit.com/r/preppers/top/.rss?t=day'
        ]
        
        # A fake "browser" tag so Reddit doesn't block our robot
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        
        for url in urls:
            response = requests.get(url, headers=headers)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                text = (entry.title).lower()
                if any(word in text for word in keywords):
                    threat_count += 1
                    
        # Normalize to 100 (if 15 top posts contain panic keywords, score is high)
        score = min((threat_count / 15) * 100, 100)
        return score
        
    except Exception as e:
        print(f"Error fetching unofficial data: {e}")
        return 50

# ---------------------------------------------------------
# 3. CORE ALGORITHM & DATA EXPORT
# ---------------------------------------------------------
def main():
    print("Fetching data and running quantitative models...")
    
    official_score = get_official_score()
    unofficial_score = get_unofficial_score()
    
    final_score = (official_score * 0.7) + (unofficial_score * 0.3)
    
    dashboard_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "global_risk_score": round(final_score, 1),
        "metrics": {
            "official_index": round(official_score, 1),
            "unofficial_index": round(unofficial_score, 1)
        },
        "status": "ELEVATED" if final_score > 60 else "STABLE"
    }
    
    with open('data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=4)
        
    print(f"Update complete. Current Score: {round(final_score, 1)}")

if __name__ == "__main__":
    main()
