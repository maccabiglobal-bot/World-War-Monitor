import json
import datetime
import requests
import yfinance as yf
import praw

# ---------------------------------------------------------
# 1. OFFICIAL SOURCES (70% Weight) - Macro & Geopolitical
# ---------------------------------------------------------
def get_official_score():
    score = 0
    
    try:
        # A. Volatility Index (VIX) - Measures global market anxiety
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[0]
        vix_score = min((vix / 40) * 100, 100) # Normalizing: VIX > 40 is extreme panic
        
        # B. Crude Oil (CL=F) - Proxy for supply chain/military logistics stress
        oil = yf.Ticker("CL=F").history(period="5d")
        oil_trend = (oil['Close'].iloc[-1] - oil['Close'].iloc[0]) / oil['Close'].iloc[0]
        oil_score = 50 + (oil_trend * 500) # Spikes in oil increase the score
        
        # C. Gold (GC=F) - Safe-haven asset hoarding
        gold = yf.Ticker("GC=F").history(period="5d")
        gold_trend = (gold['Close'].iloc[-1] - gold['Close'].iloc[0]) / gold['Close'].iloc[0]
        gold_score = 50 + (gold_trend * 500)
        
        # Aggregate Official Score (capped between 0 and 100)
        score = (vix_score * 0.4) + (oil_score * 0.3) + (gold_score * 0.3)
        return max(0, min(100, score))
        
    except Exception as e:
        print(f"Error fetching official data: {e}")
        return 50 # Default baseline if API fails

# ---------------------------------------------------------
# 2. UNOFFICIAL SOURCES (30% Weight) - OSINT & Social Sentiment
# ---------------------------------------------------------
def get_unofficial_score():
    # Note: Create a free app on Reddit (reddit.com/prefs/apps) to get these credentials
    reddit = praw.Reddit(
        client_id='YOUR_REDDIT_CLIENT_ID',
        client_secret='YOUR_REDDIT_SECRET',
        user_agent='world_war_monitor_v1'
    )
    
    keywords = ['world war', 'ww3', 'draft', 'mobilization', 'nuclear', 'defcon']
    threat_count = 0
    
    try:
        # Scan top posts in geopolitical subreddits over the last 24 hours
        for submission in reddit.subreddit('worldnews+geopolitics+preppers').top(time_filter='day', limit=100):
            text = (submission.title + " " + submission.selftext).lower()
            if any(word in text for word in keywords):
                threat_count += 1
                
        # Normalize to 100 (e.g., if 30 out of 100 top posts contain panic keywords, score is high)
        score = min((threat_count / 30) * 100, 100)
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
    
    # Apply the 70/30 weighting framework
    final_score = (official_score * 0.7) + (unofficial_score * 0.3)
    
    # Prepare the JSON payload for the frontend dashboard
    dashboard_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "global_risk_score": round(final_score, 1),
        "metrics": {
            "official_index": round(official_score, 1),
            "unofficial_index": round(unofficial_score, 1)
        },
        "status": "ELEVATED" if final_score > 60 else "STABLE"
    }
    
    # Save to data.json (Vercel/Netlify will read this file to render the site)
    with open('data.json', 'w') as f:
        json.dump(dashboard_data, f, indent=4)
        
    print(f"Update complete. Current World War Probability Score: {round(final_score, 1)}")

if __name__ == "__main__":
    main()
