import argparse
import os
import requests
import json
import re
import io
from datetime import datetime
from urllib.parse import urlparse, urljoin

# --- Specialized Tool Imports ---
import yt_dlp
import gdown
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# --- Selenium for the Generic Fallback Case ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration for Google Drive API ---
# This defines what your script is allowed to do. 'drive.readonly' is safest.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def sanitize_filename(name):
    """Removes invalid characters from a string so it can be a valid filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def download_from_youtube(url, output_dir):
    """Uses yt-dlp to handle downloading from YouTube and many other video sites."""
    print("--- YouTube URL detected. Using yt-dlp for best results. ---")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': False,
        'cookiesfrombrowser':('chrome',) 
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\nYouTube download complete.")
    except Exception as e:
        print(f"\n--- An Error Occurred with yt-dlp ---\nDetails: {e}")

def download_google_drive_private_file(file_url, output_dir):
    """(Fallback Method) Downloads a private file from Google Drive using the official API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("A browser window will now open for you to log in and grant permission.")
            # Ensure credentials.json is in the same directory as the script
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('drive', 'v3', credentials=creds)
        file_id = file_url.split('/d/')[1].split('/')[0]
        file_metadata = service.files().get(fileId=file_id).execute()
        file_name = sanitize_filename(file_metadata.get('name'))
        output_path = os.path.join(output_dir, file_name)
        
        print(f"Found private file: '{file_name}'")
        print(f"Preparing to download to: {output_path}")

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"\rDownload progress: {int(status.progress() * 100)}%", end='')
        print("\nDownload complete. Writing to file...")
        with open(output_path, 'wb') as f:
            f.write(fh.getvalue())
        print(f"Successfully saved to {output_path}")
    except HttpError as error:
        print(f'An API error occurred: {error}')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')

def download_from_google_drive(url, output_dir):
    """Attempts to download from Google Drive, trying gdown first and falling back to the API."""
    print("--- Google Drive URL detected. ---")
    print("Step 1: Attempting fast download with gdown (for public/shared files)...")
    try:
        # gdown requires the output path to be a directory
        output_path = gdown.download(url, output=output_dir, fuzzy=True, quiet=False)
        if output_path:
             print(f"\nSuccess with gdown! File saved to: {output_path}")
             return
        else:
            raise Exception("gdown returned None, indicating failure (likely a private file).")
    except Exception as e:
        print(f"gdown failed: {e}")
        print("\nStep 2: Falling back to Google Drive API for private files.")
        print("This requires `credentials.json` and may require one-time browser authentication.")
        download_google_drive_private_file(url, output_dir)

def download_generic_video_with_selenium(url, output_dir):
    """Connects to a live Chrome session to find and download a video."""
    print("--- Attempting generic download using Selenium for unknown site... ---")
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        print("Successfully connected to the browser.")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        video_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        source_element = video_element.find_element(By.TAG_NAME, "source")
        video_url = source_element.get_attribute('src')
        
        if not video_url:
            print("Error: Found a video tag, but it has no 'src' link inside.")
            return

        absolute_video_url = urljoin(url, video_url)
        default_video_name = os.path.basename(urlparse(absolute_video_url).path)
        video_name = default_video_name

        try:
            video_title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
            clean_title = sanitize_filename(video_title)
            video_name = f"{clean_title}.mp4"
        except Exception:
            print("Could not find a title (H1 tag). Using default filename.")

        output_path = os.path.join(output_dir, video_name)
        print(f"\nFound video link: {absolute_video_url}")
        print(f"Preparing to download to: {output_path}")

        with requests.get(absolute_video_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_length = r.headers.get('content-length')
            with open(output_path, 'wb') as f:
                if total_length is None:
                    f.write(r.content)
                else:
                    dl, total_length = 0, int(total_length)
                    print("Starting download...")
                    for chunk in r.iter_content(chunk_size=8192):
                        dl += len(chunk)
                        f.write(chunk)
                        done = int(50 * dl / total_length)
                        print(f"\r[{'=' * done}{' ' * (50-done)}] {dl/1024/1024:.2f} MB", end='')
        print("\nDownload complete.")
    except Exception as e:
        print(f"\n--- AN ERROR OCCURRED (Generic Selenium Method) ---")
        print(f"This website's video player might be too complex for the generic method.")
        print(f"Details: {e}")

def universal_downloader(url, output_dir):
    """Checks the URL and dispatches to the correct download function."""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname.lower() if parsed_url.hostname else ''

    if 'youtube.com' in hostname or 'youtu.be' in hostname:
        download_from_youtube(url, output_dir)
    elif 'drive.google.com' in hostname:
        download_from_google_drive(url, output_dir)
    else:
        download_generic_video_with_selenium(url, output_dir)

if __name__ == "__main__":
    # Use os.path.expanduser to create a default path in the user's home directory
    default_output_path = os.path.join(os.path.expanduser("~"), "Videos", "DownloadedVideos")
    
    parser = argparse.ArgumentParser(
        description="The Ultimate Video Downloader. It intelligently selects the best method for YouTube, Google Drive (public and private), or other generic websites.",
        epilog="Example Usage:\n  python3 ultimate_downloader.py \"<URL>\" -o \"~/Videos/MyVids\"\n"
    )
    parser.add_argument("url", help="The full URL of the webpage containing the video.")
    parser.add_argument("-o", "--output", default=default_output_path, help=f"The directory where videos will be saved. Defaults to {default_output_path}")
    args = parser.parse_args()
    
    # Expand the tilde (~) in the output path, if the user provided one
    expanded_output_path = os.path.expanduser(args.output)
    
    os.makedirs(expanded_output_path, exist_ok=True)
    universal_downloader(args.url, expanded_output_path)
