# video_transcriber

End-to-end toolkit to:
- Download videos from YouTube, Google Drive (public/private), or generic sites
- Transcribe audio using Faster-Whisper
- Refine the transcription using Google’s Generative AI (Gemini)

This repo includes:
- generic_video_downloader.py – universal downloader (YouTube, Google Drive, generic via Selenium)
- transcribe.py – transcribes audio/video to text using faster-whisper
- refine_transcription.py – refines raw transcript using google-generativeai
- download_and_transcribe.sh – one-shot bash script that chains everything
- requirements.txt – Python dependencies

## Quick start

Prerequisites:
- Python 3.10+ recommended
- pip
- Google Chrome installed (for Selenium generic fallback)
- Optional: NVIDIA GPU + CUDA for faster transcription

Setup:
```bash
# 1) Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you intend to use the Google Drive private-file fallback, you also need OAuth client credentials:
- Go to Google Cloud Console -> APIs & Services -> Credentials
- Create OAuth client ID (Desktop app)
- Download JSON and save as credentials.json in the project root
- On first use, a browser window will prompt you to sign in; a token.json will be created

Important: Do not commit credentials.json or token.json.

## Environment variables

Set your Google Generative AI key for refinement:
- GOOGLE_API_KEY – your Gemini API key from https://aistudio.google.com/app/apikey

Examples:
```bash
# macOS/Linux
export GOOGLE_API_KEY="YOUR_KEY"

# Windows (PowerShell)
setx GOOGLE_API_KEY "YOUR_KEY"
```

## Usage

There are three common ways to run the pipeline.

1) One-shot: download, transcribe, refine
- Script: download_and_transcribe.sh
- Usage:
```bash
# Make executable on macOS/Linux
chmod +x download_and_transcribe.sh

# Run: provide a video URL and optional output filename for the refined transcript
./download_and_transcribe.sh "https://www.youtube.com/watch?v=..." refined_transcription.txt
```
What it does:
- Creates a temporary working directory
- Downloads the video via generic_video_downloader.py
- Transcribes to raw_transcription.txt via transcribe.py
- Refines with refine_transcription.py to your chosen output file
- Cleans up temporary files

2) Manual: download only
- Script: generic_video_downloader.py
- Usage:
```bash
python generic_video_downloader.py "<URL>" -o "/path/to/output_dir"
```
Supported:
- YouTube: uses yt-dlp
- Google Drive:
  - Public/shared: gdown
  - Private: falls back to Google Drive API using credentials.json and token.json
- Generic sites: Selenium connects to a running Chrome instance to find <video> src and streams it to disk

Notes for Selenium generic method:
- It attaches to a running Chrome via remote debugging at 127.0.0.1:9222
- Start Chrome with debugging enabled, for example:
```bash
# macOS example
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222

# Linux example
google-chrome --remote-debugging-port=9222

# Windows example (PowerShell)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

3) Manual: transcribe and refine
- Transcribe an existing media file:
```bash
python transcribe.py /path/to/video_or_audio.ext > raw_transcription.txt
```
- Refine the raw transcript:
```bash
python refine_transcription.py raw_transcription.txt refined_transcription.txt
```

## File overview

- generic_video_downloader.py
  - Uses yt-dlp for YouTube
  - Uses gdown for public Google Drive links
  - Falls back to Google Drive API for private Drive files
  - Generic fallback via Selenium to read <video> source and download
  - Uses cookiesfrombrowser=('chrome',) with yt-dlp to leverage local Chrome cookies when present

- transcribe.py
  - Uses faster-whisper
  - Defaults: WHISPER_MODEL='medium', DEVICE='cpu', COMPUTE_TYPE='int8'
  - Prints transcript to stdout

- refine_transcription.py
  - Requires GOOGLE_API_KEY in environment
  - Uses google-generativeai (Gemini) with model "gemini-2.5-flash"
  - Writes refined output to a specified file

- download_and_transcribe.sh
  - Bash script that chains the above steps end-to-end

## Requirements

requirements.txt:
```text
requests
yt-dlp
gdown
google-auth
google-auth-oauthlib
google-api-python-client
selenium
webdriver-manager
google-generativeai
faster-whisper
```

Install with:
```bash
python -m pip install -r requirements.txt
```

Notes:
- yt-dlp is the package name, import is yt_dlp
- webdriver-manager helps auto-download the right ChromeDriver for your installed Chrome version
- faster-whisper runs on CPU by default. For GPU acceleration:
  - Install a matching PyTorch with CUDA first (see https://pytorch.org/get-started/locally/)
  - Then install faster-whisper. Set DEVICE='cuda' in transcribe.py

## Google Drive private files

To download private Drive files:
1) Enable the Google Drive API in your Google Cloud project
2) Place the downloaded OAuth client file as credentials.json in the project root
3) On first run, a browser will prompt consent; token.json will be created

Security:
- Add credentials.json and token.json to .gitignore
- Treat token.json as a secret; it contains refresh tokens

## Troubleshooting

- Selenium cannot connect to Chrome
  - Ensure Chrome is running with --remote-debugging-port=9222
  - Verify no firewall/process blocks 127.0.0.1:9222

- yt-dlp login-only videos fail
  - Ensure cookiesfrombrowser=('chrome',) works (Chrome must be your default profile or adapt profile settings)
  - Consider running yt-dlp directly to confirm site support

- Google Drive: gdown fails for private links
  - That’s expected; the script falls back to the official API if credentials.json is configured

- faster-whisper runs slowly
  - Try a smaller model (e.g., 'small' or 'base')
  - Use GPU with DEVICE='cuda' if available
  - Adjust compute type (e.g., 'float16' with CUDA)

- google-generativeai errors about API key
  - Ensure GOOGLE_API_KEY is set and exported in the same shell session
  - Check your account quota and model name

## Privacy and safety

- The repository code contains no personal information
- Do not commit credentials.json or token.json
- The downloader may use your local Chrome cookies when available; these are not embedded in the code or repo
- When sharing outputs, ensure transcripts do not include sensitive information inadvertently present in the source audio

## Example end-to-end session

```bash
# 0) Setup
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export GOOGLE_API_KEY="YOUR_KEY"

# 1) Start Chrome with remote debugging
google-chrome --remote-debugging-port=9222

# 2) Run one-shot pipeline
./download_and_transcribe.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" my_refined.txt

# 3) View result
cat my_refined.txt
```

## License

The Unlicense

## Warning ⚠️
Entire Code and this readme has been generated by AI models
Use at your own risk.
