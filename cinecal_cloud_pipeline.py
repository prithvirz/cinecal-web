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

GENRE_MAP = {}

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
    return current_date + timedelta(days=days_ahead)

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

def fetch_genre_map(api_key):
    global GENRE_MAP
    data = tmdb_request("genre/movie/list", {"language": "en-US"}, api_key)
    for g in data.get("genres", []):
        GENRE_MAP[g["id"]] = g["name"]
    tv_data = tmdb_request("genre/tv/list", {"language": "en-US"}, api_key)
    for g in tv_data.get("genres", []):
        GENRE_MAP[g["id"]] = g["name"]

def get_genre_names(genre_ids):
    return [GENRE_MAP.get(gid, "") for gid in (genre_ids or []) if GENRE_MAP.get(gid)]

def get_language_group(lang_code):
    for group, langs in LANG_GROUPS.items():
        if lang_code in langs:
            return group
    return "International"

def poster_url(path, size="w342"):
    if path:
        return f"https://image.tmdb.org/t/p/{size}{path}"
    return ""

def star_rating(vote):
    if not vote:
        return "NR"
    stars = round(vote / 2)
    return "⭐" * stars + f" {vote:.1f}/10"

def popularity_tier(pop):
    if not pop:
        return ""
    if pop >= 100:
        return "🔥"
    if pop >= 50:
        return "📈"
    return ""

def send_telegram_message(bot_token, chat_id, text_message):
    if not bot_token or not chat_id:
        print("Telegram Bot Token or Chat ID missing. Skipping.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text_message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            print("Telegram message delivered successfully!")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}", file=sys.stderr)

def send_telegram_photo(bot_token, chat_id, photo_url, caption):
    if not bot_token or not chat_id or not photo_url:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = json.dumps({
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return True
    except Exception as e:
        print(f"Failed to send photo: {e}", file=sys.stderr)
        return False

def format_movie_line(m):
    title = m.get("title") or m.get("name") or "Unknown"
    orig = m.get("original_title") or ""
    rating = star_rating(m.get("vote_average"))
    pop_tier = popularity_tier(m.get("popularity"))
    genres = ", ".join(get_genre_names(m.get("genre_ids", [])))
    lang = (m.get("original_language") or "").upper()
    line = f"• *{title}* {pop_tier}"
    if orig and orig != title:
        line += f" ({orig})"
    line += f"\n  {rating}"
    if genres:
        line += f" | {genres}"
    if lang:
        line += f" | [{lang}]"
    purl = poster_url(m.get("poster_path"), "w185")
    if purl:
        line += f"\n  🖼 [Poster]({purl})"
    if m.get("overview"):
        snippet = m["overview"][:120].replace("\n", " ").strip()
        if len(m["overview"]) > 120:
            snippet += "…"
        line += f"\n  _{snippet}_"
    return line

def format_tv_line(t):
    title = t.get("name") or "Unknown"
    orig = t.get("original_name") or ""
    rating = star_rating(t.get("vote_average"))
    pop_tier = popularity_tier(t.get("popularity"))
    genres = ", ".join(get_genre_names(t.get("genre_ids", [])))
    lang = (t.get("original_language") or "").upper()
    seasons = t.get("number_of_seasons", "?")
    episodes = t.get("number_of_episodes", "?")
    line = f"• *{title}* {pop_tier}"
    if orig and orig != title:
        line += f" ({orig})"
    line += f"\n  {rating}"
    if genres:
        line += f" | {genres}"
    if lang:
        line += f" | [{lang}]"
    line += f" | S{seasons}×{episodes}"
    purl = poster_url(t.get("poster_path"), "w185")
    if purl:
        line += f"\n  🖼 [Poster]({purl})"
    if t.get("overview"):
        snippet = t["overview"][:120].replace("\n", " ").strip()
        if len(t["overview"]) > 120:
            snippet += "…"
        line += f"\n  _{snippet}_"
    return line

def build_tldr(movies, tv_shows, market, fallback):
    parts = []
    total = len(movies) + len(tv_shows) + len(market) + len(fallback)
    if total == 0:
        return "📭 *No releases today. Quiet day at the cinema.*"
    if movies:
        lang_counts = {}
        for m in movies:
            grp = get_language_group(m.get("original_language"))
            lang_counts[grp] = lang_counts.get(grp, 0) + 1
        counts_str = ", ".join(f"{len(v)} {k}" for k, v in lang_counts.items())
        parts.append(f"🎬 {len(movies)} theatrical ({counts_str})")
    if tv_shows:
        parts.append(f"📺 {len(tv_shows)} OTT drops")
    if market:
        top_market = sorted(market, key=lambda x: x.get("popularity", 0), reverse=True)[:3]
        names = ", ".join(m.get("title", "") for m in top_market)
        parts.append(f"🌍 {len(market)} intl ({names})")
    if fallback:
        parts.append(f"📅 Friday preview: {len(fallback)} upcoming")
    return " | ".join(parts)

def build_formatted_briefing(payload):
    date_str = payload["date"]
    movies = payload["indian_theatrical_movies"]
    tv_shows = payload["indian_tv_shows"]
    market = payload["non_indian_market_context"]
    fallback = payload["friday_fallback_movies"]
    fallback_date = payload.get("friday_fallback_date")

    lines = [f"🍿 *CineCal — {date_str}*\n"]
    lines.append(build_tldr(movies, tv_shows, market, fallback))
    lines.append("")

    # Indian theatrical
    lines.append("🎬 *Indian Theatrical Releases*")
    if movies:
        by_group = {}
        for m in movies:
            grp = get_language_group(m.get("original_language"))
            by_group.setdefault(grp, []).append(m)
        for grp, items in sorted(by_group.items()):
            lines.append(f"\n📌 *{grp}* ({len(items)})")
            for m in items:
                lines.append(format_movie_line(m))
    else:
        lines.append("_No Indian theatrical releases today._")

    # OTT
    lines.append("\n📺 *OTT & Streaming*")
    if tv_shows:
        for t in tv_shows:
            lines.append(format_tv_line(t))
    else:
        lines.append("_No Indian OTT/streaming releases today._")

    # International — filtered by popularity ≥ 20 or vote_count ≥ 10
    filtered_market = [m for m in market if (m.get("popularity", 0) or 0) >= 20 or (m.get("vote_count", 0) or 0) >= 10]
    lines.append(f"\n🌐 *International Releases in India* ({len(filtered_market)} of {len(market)} shown)")
    if filtered_market:
        filtered_market.sort(key=lambda x: x.get("popularity", 0) or 0, reverse=True)
        for m in filtered_market[:8]:
            lines.append(format_movie_line(m))
        if len(filtered_market) > 8:
            lines.append(f"  _…and {len(filtered_market) - 8} more_")
    else:
        lines.append("_No significant international releases._")

    # Friday preview
    if fallback_date:
        lines.append(f"\n📅 *Friday {fallback_date} Preview*")
        if fallback:
            by_group = {}
            for m in fallback:
                grp = get_language_group(m.get("original_language"))
                by_group.setdefault(grp, []).append(m)
            total_fri = len(fallback)
            counts = ", ".join(f"{len(v)} {k}" for k, v in sorted(by_group.items()))
            lines.append(f"_{total_fri} releases: {counts}_\n")
            for grp, items in sorted(by_group.items()):
                for m in items:
                    title = m.get("title") or m.get("name") or "Unknown"
                    rating = star_rating(m.get("vote_average"))
                    pop_tier = popularity_tier(m.get("popularity"))
                    lines.append(f"• *{title}* {pop_tier} ({grp}) {rating}")
        else:
            lines.append("_No Friday releases confirmed yet._")

    lines.append(f"\n🔗 [TMDB](https://www.themoviedb.org/movie) | Generated {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M IST')}")
    return "\n".join(lines)

def run_pipeline():
    today_date = get_ist_date()
    str_date = today_date.strftime('%Y-%m-%d')
    output_dir = os.path.expanduser(f"~/cinecal_outputs/{str_date}")
    os.makedirs(output_dir, exist_ok=True)

    api_key = extract_tmdb_key()
    bot_token, chat_id = extract_telegram_config()

    if api_key:
        fetch_genre_map(api_key)

    lang_str = "|".join(INDIAN_LANGUAGES)
    exact_movies = []
    exact_tv = []
    exact_market = []
    fallback_data = []
    fallback_date_str = None

    if api_key:
        prev_date = (today_date - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (today_date + timedelta(days=1)).strftime('%Y-%m-%d')

        # Indian theatrical — no region filter, language filter is enough; no vote_count filter (upcoming = 0 votes)
        m_res = tmdb_request("discover/movie", {
            "with_original_language": lang_str,
            "primary_release_date.gte": prev_date,
            "primary_release_date.lte": next_date,
            "sort_by": "popularity.desc"
        }, api_key)
        exact_movies = [m for m in m_res.get("results", []) if m.get("release_date") == str_date]

        # Indian OTT — same approach
        t_res = tmdb_request("discover/tv", {
            "with_original_language": lang_str,
            "first_air_date.gte": prev_date,
            "first_air_date.lte": next_date,
            "sort_by": "popularity.desc"
        }, api_key)
        exact_tv = [t for t in t_res.get("results", []) if t.get("first_air_date") == str_date and "IN" in t.get("origin_country", [])]

        # International in India — keep vote_count filter to reduce noise
        market_res = tmdb_request("discover/movie", {
            "region": "IN",
            "primary_release_date.gte": prev_date,
            "primary_release_date.lte": next_date,
            "sort_by": "popularity.desc",
            "vote_count.gte": 10
        }, api_key)
        exact_market = [m for m in market_res.get("results", []) if m.get("release_date") == str_date and m.get("original_language") not in INDIAN_LANGUAGES]

        # Friday fallback
        if len(exact_movies) <= 1:
            next_fri = calculate_next_friday(today_date)
            fallback_date_str = next_fri.strftime('%Y-%m-%d')
            fri_res = tmdb_request("discover/movie", {
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

    # Save artifacts
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
            "Genres": ", ".join(get_genre_names(m.get("genre_ids", []))),
            "Popularity": m.get("popularity", 0),
            "Poster": poster_url(m.get("poster_path")),
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
            "Genres": ", ".join(get_genre_names(t.get("genre_ids", []))),
            "Popularity": t.get("popularity", 0),
            "Poster": poster_url(t.get("poster_path")),
            "Overview": t.get("overview", "").replace("\n", " ")
        })

    if csv_rows:
        with open(os.path.join(output_dir, "cinecal_releases.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Title", "Original Title", "Release Date", "Type", "Platform", "Language Group", "Rating", "Genres", "Popularity", "Poster", "Overview"])
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
            # Send top 5 posters as photos
            all_candidates = sorted(
                [m for m in exact_movies + fallback_data if m.get("poster_path")],
                key=lambda x: x.get("popularity", 0) or 0,
                reverse=True
            )
            for m in all_candidates[:5]:
                purl = poster_url(m.get("poster_path"), "w500")
                cap = f"🍿 {m.get('title') or m.get('name', '')}"
                send_telegram_photo(bot_token, chat_id, purl, cap)
    else:
        print("[SILENT]")

if __name__ == "__main__":
    run_pipeline()
