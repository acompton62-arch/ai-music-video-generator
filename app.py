from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import json
import uuid
import subprocess
import threading
import time
import shutil
from pathlib import Path
from utils.audio_processor import AudioProcessor
from utils.lyrics_parser import LyricsParser
from utils.video_generator import VideoGenerator
from utils.image_generator import ImageGenerator
from utils.scene_planner import ScenePlanner

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/output'
ALLOWED_AUDIO = {'mp3', 'wav', 'm4a'}
PROJECTS_FILE = 'static/projects.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory project state
projects = {}

def save_project(project_id, data):
    projects[project_id] = data
    try:
        all_projects = {}
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE) as f:
                all_projects = json.load(f)
        all_projects[project_id] = data
        with open(PROJECTS_FILE, 'w') as f:
            json.dump(all_projects, f)
    except Exception as e:
        print(f"Warning: could not save project: {e}")

def load_project(project_id):
    if project_id in projects:
        return projects[project_id]
    try:
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE) as f:
                all_projects = json.load(f)
            return all_projects.get(project_id)
    except:
        pass
    return None
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload and process audio file"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_AUDIO):
        return jsonify({'error': 'Invalid file type. Please upload MP3, WAV, or M4A'}), 400
    
    # Generate unique ID for this project
    project_id = str(uuid.uuid4())[:8]
    filename = f"{project_id}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Analyze audio with fallback defaults if librosa fails
    duration = 180.0
    bpm = 120.0
    beats = []
    try:
        processor = AudioProcessor(filepath)
        duration = processor.get_duration()
        bpm = processor.get_bpm()
        beats = processor.get_beat_times()
    except Exception as e:
        print(f"Audio analysis warning (using defaults): {e}")
        # Try to get duration using ffprobe as fallback
        try:
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
        except Exception as e2:
            print(f"ffprobe fallback also failed: {e2}")
    
    return jsonify({
        'success': True,
        'project_id': project_id,
        'filename': filename,
        'duration': duration,
        'bpm': round(bpm, 1),
        'beat_count': len(beats),
        'beats': beats[:50]
    })

@app.route('/api/process-lyrics', methods=['POST'])
def process_lyrics():
    """Parse lyrics and create timing segments"""
    data = request.json
    lyrics = data.get('lyrics', '')
    duration = data.get('duration', 180)  # Default 3 minutes
    
    parser = LyricsParser(lyrics, duration)
    segments = parser.parse()
    
    return jsonify({
        'success': True,
        'segments': segments,
        'total_segments': len(segments)
    })

@app.route('/api/generate-scenes', methods=['POST'])
def generate_scenes():
    """Generate scene plan based on lyrics and audio analysis"""
    data = request.json
    segments = data.get('segments', [])
    bpm = data.get('bpm', 120)
    style = data.get('style', 'cinematic')
    
    planner = ScenePlanner(segments, bpm, style)
    scenes = planner.create_scenes()
    
    return jsonify({
        'success': True,
        'scenes': scenes
    })

@app.route('/api/generate-images', methods=['POST'])
def generate_images():
    """Generate AI images for each scene"""
    data = request.json
    project_id = data.get('project_id')
    scenes = data.get('scenes', [])
    style = data.get('style', 'cinematic')
    
    generator = ImageGenerator(project_id, style)
    generated_images = []
    
    for i, scene in enumerate(scenes):
        image_path = generator.generate_scene_image(scene, i)
        generated_images.append({
            'scene_index': i,
            'image_path': image_path,
            'prompt': scene.get('visual_prompt', '')
        })
    
    return jsonify({
        'success': True,
        'images': generated_images
    })

@app.route('/api/create-video', methods=['POST'])
def create_video():
    """Compose final video with images, audio, and lyrics"""
    data = request.json
    project_id = data.get('project_id')
    audio_file = data.get('audio_file')
    scenes = data.get('scenes', [])
    images = data.get('images', [])
    show_lyrics = data.get('show_lyrics', True)
    transition_type = data.get('transition', 'fade')
    
    audio_path = os.path.join(UPLOAD_FOLDER, audio_file)
    output_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_music_video.mp4")
    
    generator = VideoGenerator(
        project_id=project_id,
        audio_path=audio_path,
        output_path=output_path,
        scenes=scenes,
        images=images,
        show_lyrics=show_lyrics,
        transition_type=transition_type
    )
    
    video_path = generator.create_video()
    
    return jsonify({
        'success': True,
        'video_path': f"/static/output/{project_id}_music_video.mp4",
        'download_url': f"/api/download/{project_id}_music_video.mp4"
    })

@app.route('/api/image-count/<project_id>')
def image_count(project_id):
    """Count how many AI images have been generated for a project"""
    images_dir = os.path.join(UPLOAD_FOLDER, f"{project_id}_images")
    if not os.path.exists(images_dir):
        return jsonify({'count': 0})
    count = len([f for f in os.listdir(images_dir) if f.endswith('.png') and 'scene_' in f])
    return jsonify({'count': count})

@app.route('/api/download/<filename>')
def download_video(filename):
    """Download the generated video"""
    return send_file(
        os.path.join(OUTPUT_FOLDER, filename),
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/status/<project_id>')
def project_status(project_id):
    """Get status of a project"""
    video_exists = os.path.exists(os.path.join(OUTPUT_FOLDER, f"{project_id}_music_video.mp4"))
    project = load_project(project_id)
    return jsonify({
        'project_id': project_id,
        'video_ready': video_exists,
        'project': project
    })

@app.route('/api/submit-image', methods=['POST'])
def submit_image():
    """Accept a pre-generated AI image for a scene"""
    project_id = request.form.get('project_id')
    scene_index = int(request.form.get('scene_index', 0))
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    
    # Save to project images folder
    images_dir = os.path.join(UPLOAD_FOLDER, f"{project_id}_images")
    os.makedirs(images_dir, exist_ok=True)
    
    image_path = os.path.join(images_dir, f"scene_{scene_index:03d}.png")
    image_file.save(image_path)
    
    return jsonify({
        'success': True,
        'image_path': image_path,
        'scene_index': scene_index
    })

@app.route('/api/save-project', methods=['POST'])
def save_project_endpoint():
    """Save project data for later video generation"""
    data = request.json
    project_id = data.get('project_id')
    save_project(project_id, data)
    return jsonify({'success': True, 'project_id': project_id})

@app.route('/api/compose-video', methods=['POST'])
def compose_video():
    """Compose video from pre-generated images already on disk"""
    data = request.json
    project_id = data.get('project_id')
    show_lyrics = data.get('show_lyrics', True)
    transition_type = data.get('transition', 'fade')

    # Load project data from projects.json if audio_file or scenes not provided
    project = load_project(project_id) or {}
    audio_file = data.get('audio_file') or project.get('audio_file')
    scenes = data.get('scenes') or project.get('scenes', [])

    # Build images list from files on disk
    images_dir = os.path.join(UPLOAD_FOLDER, f"{project_id}_images")
    images = []
    for scene in scenes:
        idx = scene['segment_index']
        image_path = os.path.join(images_dir, f"scene_{idx:03d}.png")
        if os.path.exists(image_path):
            images.append({'scene_index': idx, 'image_path': image_path})
        else:
            # Use fallback styled image
            gen = ImageGenerator(project_id, data.get('style', 'cinematic'))
            fallback_path = gen.generate_scene_image(scene, idx)
            images.append({'scene_index': idx, 'image_path': fallback_path})

    audio_path = os.path.join(UPLOAD_FOLDER, audio_file)
    output_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_music_video.mp4")

    generator = VideoGenerator(
        project_id=project_id,
        audio_path=audio_path,
        output_path=output_path,
        scenes=scenes,
        images=images,
        show_lyrics=show_lyrics,
        transition_type=transition_type
    )

    video_path = generator.create_video()

    return jsonify({
        'success': True,
        'video_path': f"/static/output/{project_id}_music_video.mp4",
        'download_url': f"/api/download/{project_id}_music_video.mp4"
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)