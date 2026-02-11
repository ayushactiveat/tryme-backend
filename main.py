from fastapi import FastAPI
from github import Github, Auth
import google.generativeai as genai
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

app = FastAPI()

# --- 🔐 CONFIGURATION ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# YouTube Config
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# Setup AI
try:
    genai.configure(api_key=GEMINI_API_KEY)
except:
    print("⚠️ Gemini Key missing")

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
    except:
        return "GitHub Connect Error"

def get_youtube_deep_dive():
    """Fetches Likes/Playlists and SAVES login so it doesn't ask again"""
    creds = None
    # 1. Check if we already logged in
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 2. If no valid login, open browser
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the login for next time!
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
        
        # Get Likes
        likes_response = youtube.videos().list(
            part="snippet", myRating="like", maxResults=5
        ).execute()
        liked_titles = [item['snippet']['title'] for item in likes_response['items']]
        
        # Get Playlists
        playlist_response = youtube.playlists().list(
            part="snippet", mine=True, maxResults=5
        ).execute()
        playlist_titles = [item['snippet']['title'] for item in playlist_response['items']]

        return {"likes": liked_titles, "playlists": playlist_titles}
    except Exception as e:
        print(f"YouTube Error: {e}")
        return {"likes": [], "playlists": []}

def generate_ai_soul(github_data, youtube_data):
    model = get_working_model()
    if not model: return "AI Sleeping."
    
    prompt = f"""
    Analyze this user deeply:
    1. 💻 Code: {github_data}
    2. 📺 Likes: {', '.join(youtube_data['likes'])}
    3. 🎵 Playlists: {', '.join(youtube_data['playlists'])}
    
    Task: Write a 1-sentence 'Vibe Check' describing their mental state.
    Style: Witty, insightful.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Vibe Unclear."

@app.get("/")
def home():
    return {"message": "TryMe Brain 4.0 (Auto-Login) is Live 🧠"}

@app.get("/vibe/{username}")
def get_user_vibe(username: str):
    github = get_github_stats(username)
    youtube = get_youtube_deep_dive()
    ai_vibe = generate_ai_soul(github, youtube)
    
    return {
        "username": username,
        "coding_focus": github,
        "youtube_obsessions": youtube['likes'],
        "youtube_playlists": youtube['playlists'],
        "ai_soul": ai_vibe
    }

# --- 💘 VIBE MATCHING LOGIC ---

# 1. The "Rival" Profile (Hardcoded for now)
SARAH_PROFILE = {
    "username": "sarah_scifi",
    "coding_focus": "Recent Repos: nasa/astropy, spacex/api",
    "youtube_obsessions": ["Interstellar Docking Scene", "SpaceX Starship Launch", "Cosmos: A Spacetime Odyssey"],
    "youtube_playlists": ["Lo-Fi Space Ambience", "Futurism Talks"],
    "ai_soul": "An optimistic futurist with her eyes on the stars and code in the cloud."
}

# 2. The Match Function
def calculate_match(user_profile, match_profile):
    model = get_working_model()
    if not model: return {"score": 0, "reason": "AI Offline"}
    
    prompt = f"""
    COMPATIBILITY CHECK:
    
    User A (The Dark Knight):
    - Vibe: {user_profile['ai_soul']}
    - Interests: {', '.join(user_profile['youtube_obsessions'])}
    
    User B (The Futurist):
    - Vibe: {match_profile['ai_soul']}
    - Interests: {', '.join(match_profile['youtube_obsessions'])}
    
    Task:
    1. Give a Compatibility Score (0-100).
    2. Write a 1-sentence "Roast & Toast" explaining why they would (or wouldn't) get along.
    
    Output Format:
    Score: [Number]
    Reason: [Sentence]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Simple parsing (AI usually returns "Score: 85\nReason: ...")
        lines = text.split('\n')
        score = lines[0].replace("Score:", "").strip()
        reason = lines[1].replace("Reason:", "").strip() if len(lines) > 1 else "Complex vibe match."
        
        return {"score": score, "reason": reason}
    except:
        return {"score": 50, "reason": "AI confused by love."}

# 3. The New Endpoint
@app.get("/match/{username}")
def get_match(username: str):
    # Get YOUR real data
    my_github = get_github_stats(username)
    my_youtube = get_youtube_deep_dive()
    my_soul = generate_ai_soul(my_github, my_youtube)
    
    my_profile = {
        "username": username,
        "ai_soul": my_soul,
        "youtube_obsessions": my_youtube['likes']
    }
    
    # Compare with Sarah
    match_result = calculate_match(my_profile, SARAH_PROFILE)
    
    return {
        "user": username,
        "match": "sarah_scifi",
        "compatibility_score": match_result['score'],
        "ai_verdict": match_result['reason']
    }