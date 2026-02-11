import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# --- ⚙️ CONFIG ---
# This file must be in the same folder!
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

def get_youtube_vibe():
    print("📺 Connecting to YouTube...")

    # 1. Authorize (Opens Browser)
    try:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)
        
        youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        print("✅ Logged in! Fetching your obsessions...\n")

        # 2. Get "Liked" Videos
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like",
            maxResults=10  # Get last 10 likes
        )
        response = request.execute()

        # 3. Analyze the Vibe
        print("--- 🎬 YOUR LAST 10 LIKES ---")
        video_titles = []
        for item in response['items']:
            title = item['snippet']['title']
            channel = item['snippet']['channelTitle']
            print(f"👍 {title} ({channel})")
            video_titles.append(f"{title} by {channel}")

        # Simple "Vibe Check" logic
        return video_titles

    except FileNotFoundError:
        print("❌ ERROR: You forgot to put 'client_secret.json' in this folder!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_youtube_vibe()