import streamlit as st
import anthropic
import json
import requests
import random
 
# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide",
)
 
# ── TMDB config ───────────────────────────────────────────────────────────────
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
 
# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [("step", 1), ("answers", {}), ("results", None), ("extra_results", None), ("bg_posters", None), ("hero_backdrop", None)]:
    if key not in st.session_state:
        st.session_state[key] = default
 
# ── TMDB helpers ──────────────────────────────────────────────────────────────
def get_tmdb_data(title, year):
    if not TMDB_API_KEY:
        return None, None, None, []
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={"api_key": TMDB_API_KEY, "query": title, "year": year, "language": "en-US"},
            timeout=5,
        )
        results = r.json().get("results", [])
        if not results:
            return None, None, None, []
        movie = results[0]
        movie_id = movie.get("id")
        poster_url = f"https://image.tmdb.org/t/p/w342{movie['poster_path']}" if movie.get("poster_path") else None
        backdrop_url = f"https://image.tmdb.org/t/p/w1280{movie['backdrop_path']}" if movie.get("backdrop_path") else None
        overview = movie.get("overview", "")
        cast = []
        if movie_id:
            credits = requests.get(
                f"https://api.themoviedb.org/3/movie/{movie_id}/credits",
                params={"api_key": TMDB_API_KEY},
                timeout=5,
            ).json()
            cast = [c["name"] for c in credits.get("cast", [])[:6]]
        return poster_url, backdrop_url, overview, cast
    except Exception:
        pass
    return None, None, None, []
 
 
def fetch_background_posters():
    """Fetch a set of popular movie posters for the background collage."""
    if not TMDB_API_KEY:
        return []
    try:
        r = requests.get(
            "https://api.themoviedb.org/3/movie/popular",
            params={"api_key": TMDB_API_KEY, "language": "en-US", "page": random.randint(1, 5)},
            timeout=5,
        )
        results = r.json().get("results", [])
        posters = [
            f"https://image.tmdb.org/t/p/w342{m['poster_path']}"
            for m in results if m.get("poster_path")
        ]
        return posters[:16]
    except Exception:
        pass
    return []
 
 
# ── Load background posters once ─────────────────────────────────────────────
if st.session_state.bg_posters is None:
    st.session_state.bg_posters = fetch_background_posters()
 
bg_posters = st.session_state.bg_posters
 
# ── Build floating poster background HTML ─────────────────────────────────────
def floating_posters_html(posters):
    if not posters:
        return ""
    items = ""
    positions = [
        (2, 5), (14, 12), (26, 3), (38, 18), (50, 6), (62, 14), (74, 2), (86, 10),
        (5, 60), (18, 72), (30, 55), (42, 68), (55, 58), (67, 74), (80, 62), (92, 70),
    ]
    rotations = [-8, 5, -4, 7, -6, 3, -9, 6, 4, -5, 8, -3, 6, -7, 4, -6]
    for idx, (left, top) in enumerate(positions):
        if idx >= len(posters):
            break
        rot = rotations[idx % len(rotations)]
        items += f"""
        <div style="
            position:absolute;
            left:{left}%;
            top:{top}%;
            width:90px;
            transform:rotate({rot}deg);
            opacity:0.09;
            border-radius:4px;
            overflow:hidden;
            pointer-events:none;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        ">
            <img src="{posters[idx]}" style="width:100%;display:block;" />
        </div>"""
    return f"""
    <div style="
        position:fixed;
        top:0; left:0; right:0; bottom:0;
        overflow:hidden;
        z-index:0;
        pointer-events:none;
        background:#0c0b0f;
    ">{items}</div>"""
 
 
def backdrop_html(url):
    if not url:
        return ""
    return f"""
    <div style="
        position:fixed;
        top:0; left:0; right:0; bottom:0;
        z-index:0;
        pointer-events:none;
        background: linear-gradient(rgba(12,11,15,0.55) 0%, rgba(12,11,15,0.82) 40%, rgba(12,11,15,0.97) 100%),
                    url('{url}') center center / cover no-repeat;
    "></div>"""
 
 
# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600&family=Outfit:wght@300;400;500&display=swap');
 
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #0c0b0f;
    color: #e8e0d5;
}
 
#MainMenu, footer, header { visibility: hidden; }
 
section[data-testid="stAppViewContainer"],
section[data-testid="stAppViewContainer"] > div:first-child,
.stApp { background-color: #0c0b0f !important; }
 
.block-container {
    padding-top: 0 !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 3rem;
    max-width: 900px;
    margin: 0 auto;
    background: transparent !important;
    position: relative;
    z-index: 1;
}
 
/* ── Top bar ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 0 0.8rem;
    border-bottom: 1px solid #2a2530;
    margin-bottom: 0;
}
.topbar-logo {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.3rem;
    font-weight: 400;
    color: #f0e8dc;
    letter-spacing: 0.15em;
}
.topbar-tag {
    font-size: 0.65rem;
    color: #c9a96e;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}
 
/* ── Hero ── */
.hero {
    text-align: center;
    padding: 2.5rem 0 2rem;
    border-bottom: 1px solid #2a2530;
    margin-bottom: 2.5rem;
    position: relative;
}
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 200px; height: 1px;
    background: linear-gradient(90deg, transparent, #c9a96e, transparent);
}
.hero-eyebrow {
    font-size: 0.65rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #c9a96e;
    margin-bottom: 0.8rem;
    font-weight: 400;
}
.hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 3.6rem;
    font-weight: 300;
    color: #f0e8dc;
    letter-spacing: 0.12em;
    line-height: 1;
    margin-bottom: 0.6rem;
}
.hero-sub {
    font-size: 0.82rem;
    color: #7a6f6a;
    font-weight: 300;
    letter-spacing: 0.08em;
}
 
/* ── Progress ── */
.progress-wrap { display: flex; gap: 5px; margin-bottom: 2rem; }
.prog-seg { height: 2px; flex: 1; border-radius: 99px; }
.prog-done   { background: #c9a96e; }
.prog-active { background: #5a4f3e; }
.prog-idle   { background: #2a2530; }
 
/* ── Step text ── */
.step-head {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.6rem;
    font-weight: 400;
    color: #f0e8dc;
    margin-bottom: 0.25rem;
    letter-spacing: 0.02em;
}
.step-hint { font-size: 0.8rem; color: #5a5055; margin-bottom: 1.2rem; font-weight: 300; }
 
/* ── Widgets ── */
div[data-testid="stMultiSelect"] > div,
div[data-testid="stSelectSlider"] > div,
div[data-testid="stSelectbox"] > div {
    background-color: #16131c !important;
    border-color: #2a2530 !important;
    color: #e8e0d5 !important;
}
div[data-testid="stMultiSelect"] label,
div[data-testid="stSelectSlider"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label {
    font-size: 0.7rem !important;
    color: #c9a96e !important;
    letter-spacing: 0.12em !important;
    font-weight: 400 !important;
    text-transform: uppercase !important;
}
div[data-testid="stRadio"] > div { gap: 6px !important; }
div[data-testid="stButton"] > button {
    background: #c9a96e;
    color: #0c0b0f;
    border: none;
    border-radius: 4px;
    padding: 0.6rem 1.8rem;
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    width: 100%;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] > button:hover { opacity: 0.78; }
 
/* ── Movie cards ── */
.movie-rank {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.8rem;
    font-weight: 300;
    color: #2a2530;
    line-height: 1;
    min-width: 42px;
    padding-top: 4px;
}
.movie-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f0e8dc;
    letter-spacing: 0.01em;
}
.movie-meta { font-size: 0.75rem; color: #5a5055; margin: 3px 0 8px; font-weight: 300; letter-spacing: 0.05em; }
.movie-why { font-size: 0.83rem; color: #9e8f88; line-height: 1.7; margin-top: 6px; font-weight: 300; }
.badge-row { display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0; }
.badge { font-size: 0.65rem; padding: 2px 9px; border-radius: 2px; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; }
.badge-genre  { background: #1e1a2e; color: #9b8fd4; border: 1px solid #2e2848; }
.badge-mood   { background: #1a2420; color: #6bab8c; border: 1px solid #243830; }
.badge-free   { background: #1a2420; color: #6bab8c; border: 1px solid #243830; }
.badge-paid   { background: #1e1a1a; color: #b06060; border: 1px solid #382424; }
.divider { border: none; border-top: 1px solid #2a2530; margin: 1.5rem 0; }
.poster-img { width: 100%; border-radius: 6px; display: block; border: 1px solid #2a2530; }
.poster-placeholder {
    width: 100%; aspect-ratio: 2/3; background: #16131c;
    border-radius: 6px; border: 1px solid #2a2530;
    display: flex; align-items: center; justify-content: center;
    color: #3a3540; font-size: 2rem; min-height: 160px;
}
</style>
""", unsafe_allow_html=True)
 
 
# ── Render background ─────────────────────────────────────────────────────────
is_results = st.session_state.step == 7
if is_results and st.session_state.hero_backdrop:
    st.markdown(backdrop_html(st.session_state.hero_backdrop), unsafe_allow_html=True)
else:
    st.markdown(floating_posters_html(bg_posters), unsafe_allow_html=True)
 
 
# ── Top bar ───────────────────────────────────────────────────────────────────
col_logo, col_action = st.columns([3, 1])
with col_logo:
    st.markdown('<div class="topbar"><span class="topbar-logo">CineMatch</span></div>', unsafe_allow_html=True)
with col_action:
    if st.session_state.step > 1:
        if st.button("↩ Start over", key="topbar_restart"):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.session_state.results = None
            st.session_state.extra_results = None
            st.session_state.hero_backdrop = None
            st.rerun()
    else:
        st.markdown('<div style="height:52px;"></div>', unsafe_allow_html=True)
 
 
# ── Hero (shown only on question steps) ───────────────────────────────────────
if st.session_state.step < 7:
    st.markdown("""
    <div class="hero">
      <div class="hero-eyebrow">Personalised Cinema</div>
      <div class="hero-title">CineMatch</div>
      <div class="hero-sub">Answer six questions &nbsp;·&nbsp; Find tonight's film</div>
    </div>
    """, unsafe_allow_html=True)
 
# ── Feature highlights (step 1 only) ─────────────────────────────────────────
if st.session_state.step == 1:
    st.markdown("""
    <div style="margin-bottom:2rem;">
      <div style="font-family:'Cormorant Garamond',serif;font-size:2rem;font-weight:300;color:#f0e8dc;text-align:center;margin-bottom:0.4rem;letter-spacing:0.02em;">
        Stop scrolling. Start watching.
      </div>
      <div style="font-size:0.85rem;color:#5a5055;text-align:center;font-weight:300;margin-bottom:2rem;letter-spacing:0.04em;">
        Tell us how you feel and we'll find the perfect film — every time.
      </div>
      <div style="border-top:1px solid #2a2530;padding-top:1.5rem;margin-bottom:0.5rem;">
        <div style="font-size:0.65rem;letter-spacing:0.2em;text-transform:uppercase;color:#c9a96e;margin-bottom:1.2rem;">Let's find your film</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
 
 
# ── Progress bar ──────────────────────────────────────────────────────────────
def render_progress(current, total=6):
    segs = ""
    for i in range(1, total + 1):
        cls = "prog-done" if i < current else ("prog-active" if i == current else "prog-idle")
        segs += f'<div class="prog-seg {cls}"></div>'
    st.markdown(f'<div class="progress-wrap">{segs}</div>', unsafe_allow_html=True)
 
 
# ── Steps ─────────────────────────────────────────────────────────────────────
def step1():
    render_progress(1)
    st.markdown('<div class="step-head">What\'s your mood tonight?</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-hint">Pick one or more</div>', unsafe_allow_html=True)
    moods = st.multiselect("Mood", ["Want to laugh", "Need to cry", "Want to be thrilled",
        "Want to think", "Want to be inspired", "Want to escape reality",
        "Want something cozy", "Want to be scared"], label_visibility="collapsed")
    if st.button("Next →", key="btn1"):
        st.session_state.answers["mood"] = moods
        st.session_state.step = 2
        st.rerun()
 
 
def step2():
    render_progress(2)
    st.markdown('<div class="step-head">Any genres you\'re feeling?</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-hint">Pick any — or skip</div>', unsafe_allow_html=True)
    genres = st.multiselect("Genres", ["Action", "Comedy", "Drama", "Sci-fi", "Horror",
        "Romance", "Thriller", "Animation", "Documentary", "Fantasy", "Crime", "Mystery"],
        label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="back2"):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("Next →", key="btn2"):
            st.session_state.answers["genre"] = genres
            st.session_state.step = 3; st.rerun()
 
 
def step3():
    render_progress(3)
    st.markdown('<div class="step-head">Time & era preferences</div>', unsafe_allow_html=True)
    runtime = st.select_slider("Maximum runtime",
        options=["Any length", "Under 90 min", "Under 2 hours", "Under 2.5 hours", "No limit"],
        value="Any length")
    era = st.multiselect("Era", ["Any era", "Classic (pre-1980)", "80s – 90s",
        "2000s – 2010s", "Recent (2020+)"], label_visibility="collapsed", placeholder="Choose an era...")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="back3"):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("Next →", key="btn3"):
            st.session_state.answers["runtime"] = runtime
            st.session_state.answers["era"] = era
            st.session_state.step = 4; st.rerun()
 
 
def step4():
    render_progress(4)
    st.markdown('<div class="step-head">Who\'s watching?</div>', unsafe_allow_html=True)
    context = st.radio("Viewing context",
        ["Just me", "Date night", "Family with kids", "Friends group"],
        label_visibility="collapsed", horizontal=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="back4"):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("Next →", key="btn4"):
            st.session_state.answers["context"] = context
            st.session_state.step = 5; st.rerun()
 
 
def step5():
    render_progress(5)
    st.markdown('<div class="step-head">How do you like your films to move?</div>', unsafe_allow_html=True)
    pacing = st.radio("Pacing",
        ["Slow burn & atmospheric", "Steady & well-paced", "Fast-paced & non-stop"],
        label_visibility="collapsed", horizontal=True)
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="step-head">What drives the film for you?</div>', unsafe_allow_html=True)
    driver = st.radio("Film driver",
        ["Characters & dialogue", "Plot & twists", "Action & spectacle", "Visuals & atmosphere"],
        label_visibility="collapsed", horizontal=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="back5"):
            st.session_state.step = 4; st.rerun()
    with col2:
        if st.button("Next →", key="btn5"):
            st.session_state.answers["pacing"] = pacing
            st.session_state.answers["driver"] = driver
            st.session_state.step = 6; st.rerun()
 
 
def step6():
    render_progress(6)
    st.markdown('<div class="step-head">Any dealbreakers or must-haves?</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-hint">Optional — skip if none apply</div>', unsafe_allow_html=True)
    filters = st.multiselect("Filters",
        ["No subtitles", "Subtitles fine", "Avoid graphic violence", "Avoid strong language",
         "Based on a true story", "Award-winning", "Underrated gem", "Cult classic"],
        label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", key="back6"):
            st.session_state.step = 5; st.rerun()
    with col2:
        if st.button("🎬  Find my movies", key="btn6"):
            st.session_state.answers["filters"] = filters
            st.session_state.step = 7; st.rerun()
 
 
# ── Anthropic calls ───────────────────────────────────────────────────────────
def fetch_recommendations(answers):
    a = answers
    prompt = f"""You are a world-class film curator. Based on these viewer preferences, recommend exactly 10 movies ranked from best match (#1) to good match (#10).
 
Preferences:
- Mood: {', '.join(a.get('mood', [])) or 'no preference'}
- Genres: {', '.join(a.get('genre', [])) or 'any'}
- Runtime: {a.get('runtime', 'any')}
- Era: {', '.join(a.get('era', [])) or 'any'}
- Watching with: {a.get('context', 'not specified')}
- Pacing preference: {a.get('pacing', 'not specified')}
- What drives the film: {a.get('driver', 'not specified')}
- Filters/preferences: {', '.join(a.get('filters', [])) or 'none'}
 
For each movie include the main US streaming platforms where it is most likely currently available (choose from: Netflix, Hulu, Disney+, Max, Apple TV+, Prime Video, Peacock, Paramount+, Tubi, Pluto TV). Mark free: true for ad-supported/free platforms (Tubi, Pluto TV, Peacock free tier) and free: false for subscription platforms.
 
Respond ONLY with a valid JSON array (no markdown, no explanation) of exactly 10 objects in ranked order:
[
  {{
    "title": "Movie Title",
    "year": 1999,
    "runtime": "2h 16m",
    "genres": ["Genre1", "Genre2"],
    "why": "One compelling sentence explaining why this is the top match.",
    "mood_tags": ["tag1", "tag2"],
    "streaming": [
      {{"platform": "Netflix", "free": false}},
      {{"platform": "Tubi", "free": true}}
    ]
  }}
]"""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)
 
 
def fetch_more_recommendations(answers, existing_titles):
    a = answers
    exclude = ", ".join(existing_titles)
    prompt = f"""You are a world-class film curator. Recommend 10 MORE movies based on these preferences but NOT including the already-recommended ones.
 
Preferences:
- Mood: {', '.join(a.get('mood', [])) or 'no preference'}
- Genres: {', '.join(a.get('genre', [])) or 'any'}
- Runtime: {a.get('runtime', 'any')}
- Era: {', '.join(a.get('era', [])) or 'any'}
- Watching with: {a.get('context', 'not specified')}
- Pacing preference: {a.get('pacing', 'not specified')}
- What drives the film: {a.get('driver', 'not specified')}
- Filters/preferences: {', '.join(a.get('filters', [])) or 'none'}
 
Already recommended (do NOT include): {exclude}
 
For each movie include US streaming platforms (Netflix, Hulu, Disney+, Max, Apple TV+, Prime Video, Peacock, Paramount+, Tubi, Pluto TV). Mark free: true for Tubi, Pluto TV, Peacock free tier.
 
Respond ONLY with a valid JSON array (no markdown) of exactly 10 objects:
[
  {{
    "title": "Movie Title",
    "year": 1999,
    "runtime": "2h 16m",
    "genres": ["Genre1", "Genre2"],
    "why": "One sentence explaining why this is a great follow-on recommendation.",
    "mood_tags": ["tag1", "tag2"],
    "streaming": [{{"platform": "Netflix", "free": false}}]
  }}
]"""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)
 
 
# ── Results page ──────────────────────────────────────────────────────────────
def step_results():
    if st.session_state.results is None:
        with st.spinner("Curating your personal cinema list..."):
            try:
                st.session_state.results = fetch_recommendations(st.session_state.answers)
                st.session_state.extra_results = None
                # Fetch backdrop for #1 movie
                m1 = st.session_state.results[0]
                _, backdrop, _, _ = get_tmdb_data(m1["title"], m1.get("year", ""))
                st.session_state.hero_backdrop = backdrop
                st.rerun()
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                if st.button("Try again"):
                    st.session_state.step = 6; st.rerun()
                return
 
    all_movies = st.session_state.results + (st.session_state.extra_results or [])
 
    st.markdown('<div class="step-head">Your Top 10</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#9e8f88;margin-bottom:1.5rem;font-weight:300;">Ranked by how well they match your preferences</div>', unsafe_allow_html=True)
 
    for i, m in enumerate(all_movies, 1):
        poster_url, _, overview, cast = get_tmdb_data(m["title"], m.get("year", ""))
 
        col_poster, col_info = st.columns([1, 3])
 
        with col_poster:
            if poster_url:
                st.markdown(f'<img src="{poster_url}" class="poster-img" alt="{m["title"]} poster">', unsafe_allow_html=True)
            else:
                st.markdown('<div class="poster-placeholder">🎬</div>', unsafe_allow_html=True)
 
        with col_info:
            genre_badges = "".join(f'<span class="badge badge-genre">{g}</span>' for g in m.get("genres", []))
            mood_badges  = "".join(f'<span class="badge badge-mood">{t}</span>'  for t in m.get("mood_tags", []))
            streaming = m.get("streaming", [])
            stream_badges = "".join(
                f'<span class="badge {"badge-free" if s.get("free") else "badge-paid"}">'
                f'{s["platform"]} · {"free" if s.get("free") else "sub"}</span>'
                for s in streaming
            ) if streaming else '<span style="font-size:0.72rem;color:#3a3540;font-style:italic;">No streaming info</span>'
 
            rank_str = f"0{i}" if i < 10 else str(i)
            trophy = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "")
            trophy_html = f'<span style="font-size:1.4rem;line-height:1;margin-left:6px;">{trophy}</span>' if trophy else ""
 
            st.markdown(f"""
            <div style="padding:4px 0 8px;">
              <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:2px;">
                <span class="movie-rank">{rank_str}</span>
                <span class="movie-title">{m['title']}</span>{trophy_html}
              </div>
              <div class="movie-meta">{m.get('year','')} &nbsp;·&nbsp; {m.get('runtime','')}</div>
              <div class="badge-row">{genre_badges}{mood_badges}</div>
              <div class="movie-why">{m.get('why','')}</div>
              <div class="badge-row" style="margin-top:10px;">{stream_badges}</div>
            </div>
            """, unsafe_allow_html=True)
 
            with st.expander("Premise & cast"):
                if overview:
                    st.markdown('<p style="color:#c9a96e;font-size:0.75rem;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Premise</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="color:#e8e0d5;font-size:0.88rem;line-height:1.7;">{overview}</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p style="color:#5a5055;font-size:0.85rem;">No premise available.</p>', unsafe_allow_html=True)
                if cast:
                    st.markdown('<p style="color:#c9a96e;font-size:0.75rem;letter-spacing:0.1em;text-transform:uppercase;margin:12px 0 6px;">Starring</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="color:#e8e0d5;font-size:0.88rem;">{" · ".join(cast)}</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p style="color:#5a5055;font-size:0.85rem;">Cast info unavailable.</p>', unsafe_allow_html=True)
 
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
 
    # ── Show more / Start over ─────────────────────────────────────────────────
    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✦  Show 10 more similar films", key="show_more"):
            with st.spinner("Finding more films you'll love..."):
                try:
                    existing = [m["title"] for m in all_movies]
                    new_batch = fetch_more_recommendations(st.session_state.answers, existing)
                    if st.session_state.extra_results:
                        st.session_state.extra_results += new_batch
                    else:
                        st.session_state.extra_results = new_batch
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't load more: {e}")
    with col2:
        if st.button("↩  Start over", key="restart"):
            st.session_state.step = 1
            st.session_state.answers = {}
            st.session_state.results = None
            st.session_state.extra_results = None
            st.session_state.hero_backdrop = None
            st.rerun()
 
 
# ── Router ────────────────────────────────────────────────────────────────────
step = st.session_state.step
if   step == 1:
    step1()
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:2.5rem;">
      <div style="border:1px solid #2a2530;border-radius:8px;padding:1.2rem;background:rgba(22,19,28,0.6);">
        <div style="font-size:1.3rem;margin-bottom:0.6rem;">🏆</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1rem;font-weight:600;color:#f0e8dc;margin-bottom:0.35rem;">Your top 10, ranked</div>
        <div style="font-size:0.78rem;color:#5a5055;line-height:1.6;font-weight:300;">Not a random list — a curated ranking from best match to great option, just for you.</div>
      </div>
      <div style="border:1px solid #2a2530;border-radius:8px;padding:1.2rem;background:rgba(22,19,28,0.6);">
        <div style="font-size:1.3rem;margin-bottom:0.6rem;">📺</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1rem;font-weight:600;color:#f0e8dc;margin-bottom:0.35rem;">Where to watch</div>
        <div style="font-size:0.78rem;color:#5a5055;line-height:1.6;font-weight:300;">Every recommendation shows which streaming platforms carry it — and whether it's free.</div>
      </div>
      <div style="border:1px solid #2a2530;border-radius:8px;padding:1.2rem;background:rgba(22,19,28,0.6);">
        <div style="font-size:1.3rem;margin-bottom:0.6rem;">🎯</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1rem;font-weight:600;color:#f0e8dc;margin-bottom:0.35rem;">AI-powered picks</div>
        <div style="font-size:0.78rem;color:#5a5055;line-height:1.6;font-weight:300;">Claude analyses your mood, taste, and energy to rank films made for this exact moment.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
elif step == 2: step2()
elif step == 3: step3()
elif step == 4: step4()
elif step == 5: step5()
elif step == 6: step6()
elif step == 7: step_results()
  
