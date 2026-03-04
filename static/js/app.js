// ============================================================
// AI Music Video Generator - Frontend
// ============================================================

const state = {
    audioFile: null,
    audioInfo: null,
    lyrics: '',
    selectedStyle: 'cinematic',
    projectData: null,
    isGenerating: false,
    generationMode: 'ai' // 'ai' = agent generates images, 'local' = local styled images
};

const elements = {
    audioUploadArea: document.getElementById('audioUploadArea'),
    audioInput: document.getElementById('audioInput'),
    audioInfo: document.getElementById('audioInfo'),
    audioFileName: document.getElementById('audioFileName'),
    audioMeta: document.getElementById('audioMeta'),
    removeAudio: document.getElementById('removeAudio'),
    lyricsInput: document.getElementById('lyricsInput'),
    lyricsCounter: document.getElementById('lyricsCounter'),
    clearLyrics: document.getElementById('clearLyrics'),
    styleOptions: document.querySelectorAll('.style-option'),
    showLyrics: document.getElementById('showLyrics'),
    autoSync: document.getElementById('autoSync'),
    transitionStyle: document.getElementById('transitionStyle'),
    generateBtn: document.getElementById('generateBtn'),
    uploadSection: document.getElementById('uploadSection'),
    progressSection: document.getElementById('progressSection'),
    resultsSection: document.getElementById('resultsSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    progressPercent: document.getElementById('progressPercent'),
    resultVideo: document.getElementById('resultVideo'),
    downloadBtn: document.getElementById('downloadBtn'),
    newVideoBtn: document.getElementById('newVideoBtn'),
    videoDuration: document.getElementById('videoDuration'),
    videoStyle: document.getElementById('videoStyle'),
    videoScenes: document.getElementById('videoScenes'),
    scenesPreview: document.getElementById('scenesPreview'),
    scenesGrid: document.getElementById('scenesGrid')
};

function init() {
    setupEventListeners();
    updateUI();
}

function setupEventListeners() {
    elements.audioUploadArea.addEventListener('click', () => elements.audioInput.click());
    elements.audioUploadArea.addEventListener('dragover', handleDragOver);
    elements.audioUploadArea.addEventListener('dragleave', handleDragLeave);
    elements.audioUploadArea.addEventListener('drop', handleDrop);
    elements.audioInput.addEventListener('change', handleAudioSelect);
    elements.removeAudio.addEventListener('click', handleRemoveAudio);
    elements.lyricsInput.addEventListener('input', handleLyricsInput);
    elements.clearLyrics.addEventListener('click', handleClearLyrics);
    elements.styleOptions.forEach(option => option.addEventListener('click', handleStyleSelect));
    elements.generateBtn.addEventListener('click', handleGenerate);
    elements.newVideoBtn.addEventListener('click', handleNewVideo);
}

// ---- Audio Handling ----
function handleDragOver(e) { e.preventDefault(); elements.audioUploadArea.classList.add('drag-over'); }
function handleDragLeave(e) { e.preventDefault(); elements.audioUploadArea.classList.remove('drag-over'); }
function handleDrop(e) {
    e.preventDefault();
    elements.audioUploadArea.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) processAudioFile(e.dataTransfer.files[0]);
}
function handleAudioSelect(e) {
    if (e.target.files.length > 0) processAudioFile(e.target.files[0]);
}

function processAudioFile(file) {
    const validExts = /\.(mp3|wav|m4a)$/i;
    if (!validExts.test(file.name)) {
        showToast('Please upload a valid audio file (MP3, WAV, or M4A)', 'error');
        return;
    }
    state.audioFile = file;
    elements.audioFileName.textContent = file.name;
    elements.audioMeta.textContent = formatFileSize(file.size);
    elements.audioUploadArea.classList.add('hidden');
    elements.audioInfo.classList.remove('hidden');
    uploadAndAnalyzeAudio();
}

function handleRemoveAudio() {
    state.audioFile = null;
    state.audioInfo = null;
    elements.audioUploadArea.classList.remove('hidden');
    elements.audioInfo.classList.add('hidden');
    updateUI();
}

async function uploadAndAnalyzeAudio() {
    try {
        const formData = new FormData();
        formData.append('audio', state.audioFile);
        const response = await fetch('/api/upload-audio', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.success) {
            state.audioInfo = data;
            elements.audioMeta.textContent = `Duration: ${formatTime(data.duration)} • BPM: ${data.bpm}`;
            updateUI();
            showToast('Audio analyzed successfully!', 'success');
        } else {
            showToast('Error processing audio: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error uploading audio: ' + error.message, 'error');
    }
}

// ---- Lyrics Handling ----
function handleLyricsInput(e) {
    state.lyrics = e.target.value;
    elements.lyricsCounter.textContent = `${state.lyrics.length} characters`;
    updateUI();
}
function handleClearLyrics() {
    elements.lyricsInput.value = '';
    state.lyrics = '';
    elements.lyricsCounter.textContent = '0 characters';
    updateUI();
}

// ---- Style Selection ----
function handleStyleSelect(e) {
    const option = e.currentTarget;
    state.selectedStyle = option.dataset.style;
    elements.styleOptions.forEach(o => o.classList.remove('active'));
    option.classList.add('active');
}

// ---- Main Generation Flow ----
async function handleGenerate() {
    if (state.isGenerating) return;
    state.isGenerating = true;

    elements.uploadSection.classList.add('hidden');
    elements.progressSection.classList.remove('hidden');
    elements.resultsSection.classList.add('hidden');

    try {
        // Step 1: Process lyrics
        setStep('step1', 'active');
        updateProgress(5, 'Analyzing audio and lyrics...');
        await processLyrics();

        // Step 2: Generate scenes
        setStep('step1', 'completed');
        setStep('step2', 'active');
        updateProgress(20, 'Planning visual scenes...');
        await generateScenes();

        // Step 3: Save project for agent image generation
        setStep('step2', 'completed');
        setStep('step3', 'active');
        updateProgress(35, 'Preparing AI image generation...');
        await saveProjectForAgent();

        // Step 4: Poll for images + compose video
        setStep('step3', 'completed');
        setStep('step4', 'active');
        updateProgress(40, 'Generating AI images for each scene...');
        await waitForImagesAndCompose();

    } catch (error) {
        console.error('Generation error:', error);
        showToast('Error: ' + error.message, 'error');
        handleNewVideo();
    }

    state.isGenerating = false;
}

async function processLyrics() {
    const response = await fetch('/api/process-lyrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lyrics: state.lyrics, duration: state.audioInfo.duration })
    });
    const data = await response.json();
    if (!data.success) throw new Error('Failed to process lyrics');
    state.projectData = { ...state.projectData, segments: data.segments };
}

async function generateScenes() {
    const response = await fetch('/api/generate-scenes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            segments: state.projectData.segments,
            bpm: state.audioInfo.bpm,
            style: state.selectedStyle
        })
    });
    const data = await response.json();
    if (!data.success) throw new Error('Failed to generate scenes');
    state.projectData = { ...state.projectData, scenes: data.scenes };
}

async function saveProjectForAgent() {
    const response = await fetch('/api/save-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            project_id: state.audioInfo.project_id,
            audio_file: state.audioInfo.filename,
            scenes: state.projectData.scenes,
            segments: state.projectData.segments,
            style: state.selectedStyle,
            show_lyrics: elements.showLyrics.checked,
            transition: elements.transitionStyle.value,
            duration: state.audioInfo.duration,
            bpm: state.audioInfo.bpm,
            status: 'waiting_for_images'
        })
    });
    const data = await response.json();
    if (!data.success) throw new Error('Failed to save project');
}

async function waitForImagesAndCompose() {
    const projectId = state.audioInfo.project_id;
    const totalScenes = state.projectData.scenes.length;

    // Show the agent instructions panel
    showAgentInstructions(projectId, totalScenes);

    // Poll for video completion
    let attempts = 0;
    const maxAttempts = 300; // 5 minutes

    while (attempts < maxAttempts) {
        await sleep(2000);
        attempts++;

        // Check if video is ready
        const statusResp = await fetch(`/api/status/${projectId}`);
        const status = await statusResp.json();

        if (status.video_ready) {
            // Video is done!
            setStep('step4', 'completed');
            setStep('step5', 'active');
            updateProgress(100, 'Video ready!');
            await sleep(500);
            setStep('step5', 'completed');
            await showResults(projectId);
            return;
        }

        // Count generated images
        const imagesDir = `static/uploads/${projectId}_images`;
        const countResp = await fetch(`/api/image-count/${projectId}`);
        if (countResp.ok) {
            const countData = await countResp.json();
            const generated = countData.count || 0;
            const progress = 40 + Math.min(50, (generated / totalScenes) * 50);
            updateProgress(progress, `AI generating images... (${generated}/${totalScenes} scenes)`);
        }
    }

    throw new Error('Timed out waiting for video generation');
}

function showAgentInstructions(projectId, totalScenes) {
    // Show a helpful message in the progress section
    const existingMsg = document.getElementById('agentMsg');
    if (existingMsg) existingMsg.remove();

    const msg = document.createElement('div');
    msg.id = 'agentMsg';
    msg.className = 'agent-message';
    msg.innerHTML = `
        <div class="agent-icon">🤖</div>
        <div class="agent-text">
            <h3>AI is generating ${totalScenes} cinematic images...</h3>
            <p>The AI agent is creating high-quality images for each scene based on your lyrics and style. This takes 1-3 minutes.</p>
            <p class="agent-project-id">Project ID: <code>${projectId}</code></p>
        </div>
    `;
    document.querySelector('.progress-card').appendChild(msg);
}

async function showResults(projectId) {
    elements.progressSection.classList.add('hidden');
    elements.resultsSection.classList.remove('hidden');

    const videoPath = `/static/output/${projectId}_music_video.mp4`;
    elements.resultVideo.src = videoPath;
    elements.videoDuration.textContent = formatTime(state.audioInfo.duration);
    elements.videoStyle.textContent = state.selectedStyle.charAt(0).toUpperCase() + state.selectedStyle.slice(1);
    elements.videoScenes.textContent = state.projectData.scenes.length;
    elements.downloadBtn.href = videoPath;

    showScenesPreview();
    showToast('🎉 Music video created successfully!', 'success');
}

function showScenesPreview() {
    const scenes = state.projectData.scenes;
    const projectId = state.audioInfo.project_id;
    elements.scenesGrid.innerHTML = '';

    scenes.forEach((scene, index) => {
        const imagePath = `/static/uploads/${projectId}_images/scene_${String(index).padStart(3, '0')}.png`;
        const sceneCard = document.createElement('div');
        sceneCard.className = 'scene-card';
        sceneCard.innerHTML = `
            <div class="scene-thumbnail">
                <img src="${imagePath}?t=${Date.now()}" alt="Scene ${index + 1}" 
                     onerror="this.style.display='none'" style="width:100%;height:100%;object-fit:cover;">
            </div>
            <div class="scene-info">
                <p class="scene-number">Scene ${index + 1} • ${formatTime(scene.start_time)} - ${formatTime(scene.end_time)}</p>
                <p class="scene-text">${scene.text}</p>
            </div>
        `;
        elements.scenesGrid.appendChild(sceneCard);
    });
}

function handleNewVideo() {
    state.audioFile = null;
    state.audioInfo = null;
    state.lyrics = '';
    state.projectData = null;
    state.isGenerating = false;

    elements.audioInput.value = '';
    elements.lyricsInput.value = '';
    elements.lyricsCounter.textContent = '0 characters';
    elements.styleOptions.forEach(o => o.classList.remove('active'));
    elements.styleOptions[0].classList.add('active');
    state.selectedStyle = 'cinematic';

    elements.resultsSection.classList.add('hidden');
    elements.progressSection.classList.add('hidden');
    elements.uploadSection.classList.remove('hidden');
    elements.audioUploadArea.classList.remove('hidden');
    elements.audioInfo.classList.add('hidden');

    const agentMsg = document.getElementById('agentMsg');
    if (agentMsg) agentMsg.remove();

    updateUI();
}

// ---- UI Helpers ----
function updateUI() {
    const hasAudio = state.audioFile !== null && state.audioInfo !== null;
    const hasLyrics = state.lyrics.trim().length > 0;
    elements.generateBtn.disabled = !(hasAudio && hasLyrics);
}

function updateProgress(percent, text) {
    elements.progressFill.style.width = `${percent}%`;
    elements.progressPercent.textContent = `${Math.round(percent)}%`;
    elements.progressText.textContent = text;
}

function setStep(stepId, state) {
    const step = document.getElementById(stepId);
    if (!step) return;
    step.classList.remove('active', 'completed');
    if (state === 'active') step.classList.add('active');
    if (state === 'completed') step.classList.add('completed');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span><span>${message}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

document.addEventListener('DOMContentLoaded', init);