import json
import datetime
import os
import random
import requests
from bs4 import BeautifulSoup
import feedparser

# ---------------------------------------------------------
# 1. ISRAELI OSINT TELEGRAM SCRAPER (Hebrew)
# ---------------------------------------------------------
def scrape_telegram_osint():
    # Public web preview URLs for Telegram channels
    channels = [
        'https://t.me/s/abualiexpress',
        'https://t.me/s/salehdesk1'
    ]
    
    # Hebrew trigger words for extreme escalation
    hebrew_keywords = [
        'תקיפה', 'כוננות שיא', 'חיסול', 'טילים', 'איראן', 'משמרות המהפכה', 
        'הסלמה', 'חריג', 'פיצוצים', 'התרעה', 'מלחמה', 'בונקר', 'חיזבאללה'
    ]
    
    threat_count = 0
    headlines = []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        for url in channels:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all message text blocks in the channel
            messages = soup.find_all('div', class_='tgme_widget_message_text')
            
            # Check the latest 15 messages per channel
            for msg in messages[-15:]:
                text = msg.get_text().lower()
                is_threat = False
                for word in hebrew_keywords:
                    if word in text:
                        threat_count += 1
                        is_threat = True
                
                # If a threat is found, grab the first few words as a headline for the ticker
                if is_threat:
                    snippet = "OSINT REPORT: " + text[:60] + "..."
                    if snippet not in headlines:
                        headlines.append(snippet)
                        
        # Score calculation: Starts at baseline 40. Every trigger word adds 5 points.
        score = min(40 + (threat_count * 5), 100)
        return score, headlines
    except Exception as e:
        print(f"Telegram scrape error: {e}")
        return 50, []

# ---------------------------------------------------------
# 2. GLOBAL RSS SCRAPER (English - Political, Military, Rumors)
# ---------------------------------------------------------
def scan_global_news():
    categories = {
        "political": ['putin', 'biden', 'xi', 'khamenei', 'white house', 'kremlin', 'tehran', 'ultimatum', 'threatens', 'warns'],
        "military": ['troops', 'idf', 'irgc', 'centcom', 'nato', 'deployment', 'high alert', 'strike', 'prepares', 'warships'],
        "rumors": ['unconfirmed', 'reportedly', 'explosion', 'jamming', 'bunker', 'assassination', 'panic', 'shadow', 'secret'],
        "diplomatic": ['evacuate', 'airspace', 'flights canceled', 'embassy', 'shelter', 'citizens', 'leave immediately', 'sirens']
    }
    
    threat_counts = {k: 0 for k in categories}
    headlines = []
    
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
                is_threat = False
                for cat, keywords in categories.items():
                    if any(word in text for word in keywords):
                        threat_counts[cat] += 1
                        is_threat = True
                
                if is_threat and entry.title not in headlines:
                    headlines.append(entry.title)
                    
        # Calculate baseline category scores (Start at 40, add 6 points per hit)
        scores = {cat: min(40 + (count * 6), 100) for cat, count in threat_counts.items()}
        return scores, headlines 
        
    except Exception as e:
        return {k: 50 for k in categories}, []

# ---------------------------------------------------------
# 3. HEAT MAP DATA
# ---------------------------------------------------------
def get_map_data():
    return {
        "RU": 3, "UA": 3, "IL": 3, "LB": 3, "PS": 3, "SY": 3, "YE": 3, "SD": 3, "MM": 3, "IR": 3,
        "TW": 2, "KP": 2, "KR": 2, "SA": 2, "PK": 2, "BY": 2, "IQ": 2, "CN": 2,
        "PH": 1, "RS": 1, "VE": 1, "GY": 1, "IN": 1, "PL": 1, "DE": 1, "US": 1
    }

# ---------------------------------------------------------
# 4. CORE ALGORITHM
# ---------------------------------------------------------
def main():
    # 1. Fetch Data
    telegram_score, telegram_headlines = scrape_telegram_osint()
    global_scores, global_headlines = scan_global_news()
    
    # 2. Map to the 5 New Parameters
    ind1 = global_scores["political"]       # Political Leader Declarations (20%)
    ind2 = global_scores["military"]        # Military Command Posture (20%)
    ind3 = telegram_score                   # Middle East OSINT Telegram (20%)
    ind4 = global_scores["rumors"]          # Shadow Chatter & Rumors (20%)
    ind5 = global_scores["diplomatic"]      # Diplomatic & Civilian Emergencies (20%)
    
    # 3. Calculate Final Score (Equally weighted at 20% each)
    final_score = (ind1 * 0.20) + (ind2 * 0.20) + (ind3 * 0.20) + (ind4 * 0.20) + (ind5 * 0.20)
    
    # Combine headlines and keep the top 12 for the ticker
    all_headlines = global_headlines + telegram_headlines
    random.shuffle(all_headlines)
    live_headlines = all_headlines[:12]
    
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
            walk_score = walk_score + random.uniform(-1.5, 1.5) 
            mock_history.append({"date": past_date, "score": round(max(0, min(100, walk_score)), 1)})
        mock_history.reverse()
        history = mock_history

    history = [h for h in history if h['date'] != today_str] 
    history.append({"date": today_str, "score": round(final_score, 1)})
    history = history[-30:]
    
    dashboard_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "global_risk_score": round(final_score, 1),
        "status": "CRITICAL THREAT" if final_score > 75 else "ELEVATED THREAT" if final_score > 55 else "STABLE",
        "history": history,
        "map_data": get_map_data(),
        "headlines": live_headlines,
        "indicators": [
            {"name": "Political Leader Declarations", "score": round(ind1, 1), "weight": 20},
            {"name": "Military Command Posture", "score": round(ind2, 1), "weight": 20},
            {"name": "Middle East OSINT (Telegram)", "score": round(ind3, 1), "weight": 20},
            {"name": "Shadow Chatter & Rumors", "score": round(ind4, 1), "weight": 20},
            {"name": "Diplomatic & Civilian Action", "score": round(ind5, 1), "weight": 20}
        ]
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
