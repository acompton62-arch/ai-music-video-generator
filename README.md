# 🎬 AI Music Video Generator

Transform any MP3 and lyrics into a stunning cinematic music video with AI-generated images.

## Features

- 🎵 Upload any MP3 audio file
- 📝 Add lyrics (plain text or LRC format with timestamps)
- 🤖 AI-generated cinematic images for each scene
- 🎬 Ken Burns zoom effect on every image
- 📺 Lyrics overlay synchronized to music
- ⬇️ Download finished MP4 video (1920×1080 HD)

## Deploy to Railway (Recommended)

### One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Manual Deploy

1. **Fork or clone this repository**
2. **Go to [railway.app](https://railway.app)** and sign in with GitHub
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select this repository**
5. Railway will automatically detect the configuration and deploy!

### Environment Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | Port to run the server on (Railway sets this automatically) |
| `FLASK_ENV` | `production` | Set to `development` for debug mode |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (required for video generation)
# macOS: brew install ffmpeg
# Ubuntu: apt-get install ffmpeg
# Windows: Download from https://ffmpeg.org/download.html

# Run the app
python app.py
```

Then open http://localhost:7860 in your browser.

## How It Works

1. **Upload** your MP3 file
2. **Add lyrics** - paste plain text or LRC format
3. **Generate scenes** - the app analyzes your audio and lyrics to plan visual scenes
4. **Generate images** - AI creates cinematic images for each scene
5. **Create video** - FFmpeg composes everything into a final MP4 with your audio

## Tech Stack

- **Backend:** Python Flask
- **Audio Analysis:** librosa (BPM detection, beat tracking)
- **Image Generation:** AI image generation pipeline
- **Video Composition:** FFmpeg with Ken Burns effect
- **Frontend:** Vanilla HTML/CSS/JavaScript

## Requirements

- Python 3.11+
- FFmpeg installed on the system
- 2GB+ RAM recommended