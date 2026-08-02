import os
import sys
import json
import csv
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import pytz

LANG_GROUPS = {
    "Hindi & North Indian": ["hi", "pa"],
    "Bengali & Eastern": ["bn"],
    "South Indian": ["te", "ta", "ml", "kn"],
    "Marathi & Other Regional": ["mr"]
}

INDIAN_LANGUAGES = ["hi", "te", "ta", "ml", "kn", "pa", "bn", "mr"]

def get_ist_date():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).date()

def extract_tmdb_key():
    if os.environ.get("TMDB_API_KEY"):
        content = os.environ.get("TMDB_API_KEY").strip()
        if '|' in content:
            return content.split('|')[-1].strip()
        return content
    key_path = os.path.expanduser('~/.tmdb/api_key')
    if os.path.exists(key_path):
        with open(key_path, 'r') as f:
            content = f.read().strip()
            if '|' in content:
                return content.split('|')[-1].strip()
            return content
    return None

def extract_telegram_config():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    config_path = os.path.expanduser('~/.telegram/config')
    if (not bot_token or not chat_id) and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    bot_token = line.split("=", 1)[1].strip()
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    chat_id = line.split("=", 1)[1].strip()
    return bot_token, chat_id

def calculate_next_friday(current_date):
    days_ahead = (4 - current_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_friday = current_date + timedelta(days=days_ahead)
    assert next_friday.weekday() == 4, f"Calculated date {next_friday} is not a Friday!"
    return next_friday

def tmdb_request(endpoint, params, api_key):
    request_params = params.copy()
    is_v3_key = len(api_key) == 32 and not api_key.startswith("ey")
    if is_v3_key:
        request_params["api_key"] = api_key
    url = f"https://api.themoviedb.org/3/{endpoint}?" + urllib.parse.urlencode(request_params)
    req = urllib.request.Request(url)
    if not is_v3_key:
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"API Error ({endpoint}): {e}", file=sys.stderr)
        return {"results": []}

def get_language_group(lang_code):
    for group, langs in LANG_GROUPS.items():
        if lang_code in langs:
            return group
    return "International & Other"

def send_telegram_message(bot_token, chat_id, text_message):
    if not bot_token or not chat_id:
        print("Telegram Bot Token or Chat ID missing. Skipping Telegram notification.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text_message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            print("Telegram message delivered successfully!")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}", file=sys.stderr)

def run_pipeline():
    today_date = get_ist_date()
    str_date = today_date.strftime('%Y-%m-%d')
    output_dir = os.path.expanduser(f"~/cinecal_outputs/{str_date}")
    os.makedirs(output_dir, exist_ok=True)
    api_key = extract_tmdb_key()
    bot_token, chat_id = extract_telegram_config()
    lang_str = "|".join(INDIAN_LANGUAGES)
    exact_movies = []
    exact_tv = []
    exact_market = []
    fallback_data = []
    fallback_date_str = None
    if api_key:
        m_res = tmdb_request("discover/movie", {
            "region": "IN",
            "with_original_language": lang_str,
            "primary_release_date.gte": str_date,
            "primary_release_date.lte": str_date,
            "sort_by": "popularity.desc"
        }, api_key)
        exact_movies = [m for m in m_res.get("results", []) if m.get("release_date") == str_date]
        t_res = tmdb_request("discover/tv", {
            "with_original_language": lang_str,
            "first_air_date.gte": str_date,
            "first_air_date.lte": str_date,
            "sort_by": "popularity.desc"
        }, api_key)
        exact_tv = [t for t in t_res.get("results", []) if t.get("first_air_date") == str_date and "IN" in t.get("origin_country", [])]
        market_res = tmdb_request("discover/movie", {
            "region": "IN",
            "primary_release_date.gte": str_date,
            "primary_release_date.lte": str_date,
            "sort_by": "popularity.desc"
        }, api_key)
        exact_market = [m for m in market_res.get("results", []) if m.get("release_date") == str_date and m.get("original_language") not in INDIAN_LANGUAGES]
    if len(exact_movies) <= 1:
        next_fri = calculate_next_friday(today_date)
        fallback_date_str = next_fri.strftime('%Y-%m-%d')
        fri_res = tmdb_request("discover/movie", {
            "region": "IN",
            "with_original_language": lang_str,
            "primary_release_date.gte": fallback_date_str,
            "primary_release_date.lte": fallback_date_str,
            "sort_by": "popularity.desc"
        }, api_key)
        fallback_data = [m for m in fri_res.get("results", []) if m.get("release_date") == fallback_date_str]
    payload = {
        "date": str_date,
        "indian_theatrical_movies": exact_movies,
        "indian_tv_shows": exact_tv,
        "non_indian_market_context": exact_market,
        "friday_fallback_date": fallback_date_str,
        "friday_fallback_movies": fallback_data
    }
    with open(os.path.join(output_dir, "cinecal_releases.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    csv_rows = []
    for m in exact_movies:
        csv_rows.append({
            "Title": m.get("title", ""),
            "Original Title": m.get("original_title", ""),
            "Release Date": str_date,
            "Type": "Movie",
            "Platform": "Theatrical",
            "Language Group": get_language_group(m.get("original_language")),
            "Rating": m.get("vote_average", 0.0),
            "Poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "",
            "Overview": m.get("overview", "").replace("\n", " ")
        })
    for t in exact_tv:
        csv_rows.append({
            "Title": t.get("name", ""),
            "Original Title": t.get("original_name", ""),
            "Release Date": str_date,
            "Type": "TV Show",
            "Platform": "OTT / Streaming",
            "Language Group": get_language_group(t.get("original_language")),
            "Rating": t.get("vote_average", 0.0),
            "Poster": f"https://image.tmdb.org/t/p/w500{t.get('poster_path')}" if t.get("poster_path") else "",
            "Overview": t.get("overview", "").replace("\n", " ")
        })
    with open(os.path.join(output_dir, "cinecal_releases.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Original Title", "Release Date", "Type", "Platform", "Language Group", "Rating", "Poster", "Overview"])
        writer.writeheader()
        writer.writerows(csv_rows)
    md_content = build_formatted_briefing(payload)
    with open(os.path.join(output_dir, "cinecal_briefing.md"), "w", encoding="utf-8") as f:
        f.write(md_content)
    total_items = len(exact_movies) + len(exact_tv) + len(exact_market) + len(fallback_data)
    if total_items > 0:
        print("[DECISION] BRIEFING")
        if bot_token and chat_id:
            send_telegram_message(bot_token, chat_id, md_content)
        else:
            print("[SILENT]")

def build_formatted_briefing(payload):
    date_str = payload["date"]
    lines = [f"🍿 *CineCal Daily Briefing — {date_str}*\n"]
    lines.append("🎬 *Indian-Language Theatrical Releases*")
    theatricals = payload["indian_theatrical_movies"]
    if theatricals:
        by_group = {}
        for m in theatricals:
            grp = get_language_group(m.get("original_language"))
            by_group.setdefault(grp, []).append(m)
        for grp, items in by_group.items():
            lines.append(f"\n📌 *{grp}*")
            for m in items:
                title = m.get("title")
                rating = f"⭐ {m.get('vote_average'):.1f}/10" if m.get('vote_average') else ""
                poster = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else ""
                lines.append(f"• *{title}* {rating}")
                if poster:
                    lines.append(f" 🖼 [Poster Image]({poster})")
                if m.get("overview"):
                    lines.append(f" _{m.get('overview')[:150]}..._")
    else:
        lines.append("_No Indian theatrical releases today._")
    lines.append("\n📺 *Indian OTT & Streaming Drops*")
    tv_items = payload["indian_tv_shows"]
    if tv_items:
        for t in tv_items:
            title = t.get("name")
            lang = t.get("original_language", "").upper()
            rating = f"⭐ {t.get('vote_average'):.1f}/10" if t.get('vote_average') else ""
            lines.append(f"• *{title}* [{lang}] {rating}")
            if t.get("poster_path"):
                lines.append(f" 🖼 [Poster Image](https://image.tmdb.org/t/p/w500{t.get('poster_path')})")
    else:
        lines.append("_No Indian OTT/streaming releases today._")
    lines.append("\n🌐 *International Market Context (India Release)*")
    market_items = payload["non_indian_market_context"]
    if market_items:
        for m in market_items:
            lines.append(f"• *{m.get('title')}* [{m.get('original_language', '').upper()}]")
    else:
        lines.append("_No major international theatrical releases in India today._")
    if payload.get("friday_fallback_date"):
        lines.append(f"\n📅 *Upcoming Friday Preview ({payload['friday_fallback_date']})*")
        fallback_m = payload["friday_fallback_movies"]
        if fallback_m:
            for m in fallback_m:
                grp = get_language_group(m.get('original_language'))
                lines.append(f"• *{m.get('title')}* ({grp})")
        else:
            lines.append("_No upcoming Friday theatrical releases recorded yet._")
    return "\n".join(lines)

if __name__ == "__main__":
    run_pipeline()
