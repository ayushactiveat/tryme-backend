from fastapi import FastAPI
from github import Github, Auth
import google.generativeai as genai
import os
from datetime import datetime

app = FastAPI()

# --- 🧠 MEMORY (The Radar) ---
# This list stores everyone currently "Online"
ACTIVE_SOULS = []

# --- 🔐 CONFIGURATION ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup AI
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    else:
        print("⚠️ Gemini Key missing")
except:
    print("⚠️ Gemini Config Error")

def get_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                return genai.GenerativeModel(m.name)
        return genai.GenerativeModel('gemini-pro')
    except:
        return None

def get_github_stats(username):
    try:
        if not GITHUB_TOKEN: return "GitHub Token Missing"
        auth = Auth.Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        user = g.get_user(username)
        events = user.get_public_events()
        repos = []
        for i, event in enumerate(events):
            if i > 15: break
            repos.append(event.repo.name)
        if not repos: return "Inactive"
        return f"Recent Repos: {', '.join(set(repos[:3]))}"
    except Exception as e:
        print(f"GitHub Error: {e}")
        return "GitHub Connect Error"

def get_youtube_deep_dive():
    """Bulletproof Cloud Version"""
    if not os.path.exists("client_secret.json"):
        # print("⚠️ Cloud Mode: No YouTube secrets found. Using backup data.")
        return {
            "likes": ["Coding Tutorials", "Lo-Fi Beats", "Tech News"], 
            "playlists": ["Study Mix", "Python Mastery"]
        }
    return {"likes": [], "playlists": []}

def generate_ai_soul(github_data, youtube_data):
    model = get_working_model()
    if not model: return "AI Sleeping."
    
    prompt = f"""
    Analyze this user deeply:
    1. 💻 Code: {github_data}
    2. 📺 Likes: {', '.join(youtube_data['likes'])}
    
    Task: Write a 1-sentence 'Vibe Check' describing their mental state.
    Style: Witty, insightful.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Vibe Unclear."

# --- 📡 API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "TryMe Radar is Active 📡"}

@app.get("/vibe/{username}")
def get_user_vibe(username: str):
    # 1. Calculate Vibe
    github = get_github_stats(username)
    youtube = get_youtube_deep_dive()
    ai_vibe = generate_ai_soul(github, youtube)
    
    # 2. 🧠 RADAR MEMORY: Save user to the active list
    global ACTIVE_SOULS
    # Remove old entry if it exists (so we don't have duplicates)
    ACTIVE_SOULS = [u for u in ACTIVE_SOULS if u['username'] != username]
    
    # Add new entry with timestamp
    new_soul = {
        "username": username,
        "ai_soul": ai_vibe,
        "last_seen": str(datetime.now())
    }
    ACTIVE_SOULS.append(new_soul)
    
    return {
        "username": username,
        "coding_focus": github,
        "youtube_obsessions": youtube['likes'],
        "youtube_playlists": youtube['playlists'],
        "ai_soul": ai_vibe
    }

@app.get("/radar")
def scan_radar():
    """Returns everyone currently online (The Feed)"""
    # If empty, add ghosts so it doesn't look broken
    if len(ACTIVE_SOULS) == 0:
        return [
            {"username": "ghost_coder", "ai_soul": "Lurking in the shadows of a broken repo."},
            {"username": "system_admin", "ai_soul": "Watching the logs flow like digital rain."}
        ]
    return ACTIVE_SOULS

# --- 💘 VIBE MATCHING LOGIC (Kept for 1v1 battles) ---
SARAH_PROFILE = {
    "username": "sarah_scifi",
    "coding_focus": "Recent Repos: nasa/astropy, spacex/api",
    "youtube_obsessions": ["Interstellar Docking Scene", "SpaceX Starship Launch", "Cosmos"],
    "ai_soul": "An optimistic futurist with her eyes on the stars and code in the cloud."
}

def calculate_match(user_profile, match_profile):
    model = get_working_model()
    if not model: return {"score": 0, "reason": "AI Offline"}
    
    prompt = f"""
    COMPATIBILITY CHECK:
    User A: {user_profile['ai_soul']}
    User B: {match_profile['ai_soul']}
    
    Task:
    1. Compatibility Score (0-100).
    2. 1-sentence roast about why they fit/clash.
    
    Output Format:
    Score: [Number]
    Reason: [Sentence]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        lines = text.split('\n')
        score = 50 
        reason = "Complex vibe."
        for line in lines:
            if "Score:" in line:
                score = line.replace("Score:", "").strip()
            if "Reason:" in line:
                reason = line.replace("Reason:", "").strip()
        return {"score": score, "reason": reason}
    except:
        return {"score": 50, "reason": "AI confused."}

@app.get("/match/{username}")
def get_match(username: str):
    my_github = get_github_stats(username)
    my_youtube = get_youtube_deep_dive()
    my_soul = generate_ai_soul(my_github, my_youtube)
    
    my_profile = {"username": username, "ai_soul": my_soul, "youtube_obsessions": my_youtube['likes']}
    match_result = calculate_match(my_profile, SARAH_PROFILE)
    
    return {
        "user": username,
        "match": "sarah_scifi",
        "compatibility_score": match_result['score'],
        "ai_verdict": match_result['reason']
    }