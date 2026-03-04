import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

class VideoGenerator:
    """Composes the final music video from images, audio, and scenes"""
    
    def __init__(self, project_id: str, audio_path: str, output_path: str,
                 scenes: List[Dict], images: List[Dict], show_lyrics: bool = True,
                 transition_type: str = 'fade', fps: int = 30):
        self.project_id = project_id
        self.audio_path = audio_path
        self.output_path = output_path
        self.scenes = scenes
        self.images = images
        self.show_lyrics = show_lyrics
        self.transition_type = transition_type
        self.fps = fps
        
        # Working directories
        self.working_dir = Path(f'static/uploads/{project_id}_temp')
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for FFmpeg
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Verify FFmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE, 
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: FFmpeg not found. Video generation may be limited.")
            return False
    
    def create_video(self) -> str:
        """Main method to create the complete music video"""
        print("Starting music video generation...")
        
        try:
            # Step 1: Prepare images
            prepared_images = self._prepare_images()
            
            # Step 2: Create image sequences for each scene
            image_sequences = self._create_image_sequences(prepared_images)
            
            # Step 3: Create lyric overlays
            lyric_overlays = self._create_lyric_overlays() if self.show_lyrics else None
            
            # Step 4: Create individual scene videos
            scene_videos = self._create_scene_videos(image_sequences, lyric_overlays)
            
            # Step 5: Concatenate all scenes
            final_video = self._concatenate_videos(scene_videos)
            
            # Step 6: Add audio
            video_with_audio = self._add_audio(final_video)
            
            # Step 7: Clean up temporary files
            self._cleanup()
            
            print(f"Music video created successfully: {video_with_audio}")
            return video_with_audio
            
        except Exception as e:
            print(f"Error creating video: {e}")
            raise
    
    def _prepare_images(self) -> Dict:
        """Prepare and organize images for each scene"""
        image_map = {}
        
        for img_data in self.images:
            scene_idx = img_data['scene_index']
            image_path = img_data['image_path']
            
            if scene_idx not in image_map:
                image_map[scene_idx] = []
            
            if os.path.exists(image_path):
                image_map[scene_idx].append(image_path)
        
        return image_map
    
    def _create_image_sequences(self, prepared_images: Dict) -> Dict:
        """Create frame sequences for each scene based on duration"""
        sequences = {}
        
        for scene in self.scenes:
            scene_idx = scene['segment_index']
            duration = scene['duration']
            num_frames = int(duration * self.fps)
            
            if scene_idx not in prepared_images or not prepared_images[scene_idx]:
                print(f"Warning: No image for scene {scene_idx}")
                continue
            
            image_path = prepared_images[scene_idx][0]
            sequence_dir = self.working_dir / f'scene_{scene_idx:03d}'
            sequence_dir.mkdir(exist_ok=True)
            
            # Generate frames with Ken Burns effect or other animation
            self._generate_animated_frames(
                image_path=image_path,
                output_dir=sequence_dir,
                num_frames=num_frames,
                scene=scene
            )
            
            sequences[scene_idx] = {
                'directory': str(sequence_dir),
                'duration': duration,
                'num_frames': num_frames
            }
        
        return sequences
    
    def _generate_animated_frames(self, image_path: str, output_dir: Path, 
                                   num_frames: int, scene: Dict):
        """Generate animated frames from a single image"""
        from PIL import Image, ImageFilter
        import numpy as np
        
        # Load image
        img = Image.open(image_path)
        img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
        
        # Get camera movement settings
        movement = scene.get('camera_movement', 'slow push')
        animation_speed = scene.get('animation_speed', 1.0)
        
        # Calculate movement vectors
        if 'push in' in movement or 'push' in movement:
            dx, dy = -0.5, -0.5  # Move toward center
            zoom = 1.0 + (0.1 * animation_speed)
        elif 'pull back' in movement or 'pull' in movement:
            dx, dy = 0.5, 0.5  # Move away from center
            zoom = 1.0 - (0.05 * animation_speed)
        elif 'pan' in movement:
            dx, dy = -0.5, 0
            zoom = 1.0
        else:
            dx, dy = 0, 0
            zoom = 1.0
        
        # Generate frames
        for frame_idx in range(num_frames):
            # Calculate animation progress
            progress = frame_idx / max(num_frames - 1, 1)
            
            # Calculate current transformation
            current_dx = dx * progress * 100
            current_dy = dy * progress * 100
            current_zoom = 1.0 + (zoom - 1.0) * progress
            
            # Apply zoom
            new_width = int(1920 * current_zoom)
            new_height = int(1080 * current_zoom)
            zoomed_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Apply pan
            crop_x = int((new_width - 1920) / 2 + current_dx)
            crop_y = int((new_height - 1080) / 2 + current_dy)
            
            # Ensure crop is within bounds
            crop_x = max(0, min(crop_x, new_width - 1920))
            crop_y = max(0, min(crop_y, new_height - 1080))
            
            # Crop and save
            frame = zoomed_img.crop((crop_x, crop_y, crop_x + 1920, crop_y + 1080))
            frame_path = output_dir / f'frame_{frame_idx:06d}.png'
            frame.save(frame_path, 'PNG', quality=95)
    
    def _create_lyric_overlays(self) -> Dict:
        """Create lyric text overlays for each scene"""
        overlays = {}
        
        for scene in self.scenes:
            scene_idx = scene['segment_index']
            text = scene.get('text', '')
            
            if not text:
                continue
            
            # Create text overlay
            overlay_path = self.working_dir / f'lyrics_{scene_idx:03d}.png'
            
            try:
                self._create_text_overlay(
                    text=text,
                    output_path=overlay_path,
                    position=scene.get('text_position', {'x': 'center', 'y': 'center'}),
                    animation=scene.get('text_animation', 'fade')
                )
                
                overlays[scene_idx] = {
                    'path': str(overlay_path),
                    'duration': scene['duration'],
                    'animation': scene.get('text_animation', 'fade')
                }
            except Exception as e:
                print(f"Warning: Could not create lyric overlay for scene {scene_idx}: {e}")
        
        return overlays
    
    def _create_text_overlay(self, text: str, output_path: Path, 
                             position: Dict, animation: str):
        """Create a text overlay image"""
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        
        # Create transparent overlay
        overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Try to use a nice font, fallback to default
        try:
            font_size = 60
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x_pos = position.get('x', 'center')
        y_pos = position.get('y', 'center')
        
        if x_pos == 'center':
            x = (1920 - text_width) // 2
        elif '%' in str(x_pos):
            x = int(float(x_pos.rstrip('%')) / 100 * 1920 - text_width / 2)
        else:
            x = int(x_pos) - text_width // 2
        
        if y_pos == 'center':
            y = (1080 - text_height) // 2
        elif '%' in str(y_pos):
            y = int(float(y_pos.rstrip('%')) / 100 * 1080 - text_height / 2)
        else:
            y = int(y_pos) - text_height // 2
        
        # Draw text with shadow for better visibility
        shadow_color = (0, 0, 0, 180)
        text_color = (255, 255, 255, 255)
        
        # Shadow
        draw.text((x + 3, y + 3), text, font=font, fill=shadow_color)
        # Main text
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Add subtle background blur behind text
        bg_overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 80))
        bg_box = (x - 20, y - 20, x + text_width + 20, y + text_height + 20)
        draw_bg = ImageDraw.Draw(bg_overlay)
        draw_bg.rectangle(bg_box, fill=(0, 0, 0, 100))
        
        # Combine
        overlay = Image.alpha_composite(overlay, bg_overlay)
        
        overlay.save(output_path, 'PNG')
    
    def _create_scene_videos(self, image_sequences: Dict, lyric_overlays: Optional[Dict]) -> List[str]:
        """Create individual scene videos"""
        scene_videos = []
        
        for scene_idx, sequence_data in image_sequences.items():
            output_path = self.working_dir / f'scene_{scene_idx:03d}.mp4'
            
            # Get scene information
            scene = next((s for s in self.scenes if s['segment_index'] == scene_idx), None)
            if not scene:
                continue
            
            duration = scene['duration']
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.fps),
                '-i', f'{sequence_data["directory"]}/frame_%06d.png',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '18',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                str(output_path)
            ]
            
            # Add lyric overlay if available
            if lyric_overlays and scene_idx in lyric_overlays:
                overlay_data = lyric_overlays[scene_idx]
                cmd = [
                    'ffmpeg', '-y',
                    '-framerate', str(self.fps),
                    '-i', f'{sequence_data["directory"]}/frame_%06d.png',
                    '-i', overlay_data['path'],
                    '-filter_complex',
                    f'[0:v][1:v]overlay=0:0:enable=\'between(t,0,{duration})\'',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '18',
                    '-pix_fmt', 'yuv420p',
                    '-t', str(duration),
                    str(output_path)
                ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                scene_videos.append(str(output_path))
            except subprocess.CalledProcessError as e:
                print(f"Error creating scene {scene_idx} video: {e}")
                continue
        
        return scene_videos
    
    def _concatenate_videos(self, scene_videos: List[str]) -> str:
        """Concatenate all scene videos"""
        if not scene_videos:
            raise ValueError("No scene videos to concatenate")
        
        # Create file list
        list_file = self.working_dir / 'filelist.txt'
        
        with open(list_file, 'w') as f:
            for video_path in scene_videos:
                # Use absolute path to avoid issues
                abs_path = os.path.abspath(video_path)
                f.write(f"file '{abs_path}'\n")
        
        # Determine transition type
        if self.transition_type == 'fade':
            filter_complex = ''.join([
                f"[{i}:v]format=pix_fmts=yuva420p,fade=t=out:st={self.scenes[i]['duration']-0.5}:d=0.5:alpha=1[v{i}];"
                for i in range(len(scene_videos))
            ])[:-1] + ''.join([
                f"[v{i}]" for i in range(len(scene_videos))
            ]) + f"concat=n={len(scene_videos)}:v=1:a=0[outv]"
        else:
            filter_complex = ''.join([
                f"[{i}:v]" for i in range(len(scene_videos))
            ]) + f"concat=n={len(scene_videos)}:v=1:a=0[outv]"
        
        output_path = self.working_dir / 'concatenated.mp4'
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-filter_complex', f'concat=n={len(scene_videos)}:v=1:a=0[outv]',
            '-map', '[outv]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '20',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error concatenating videos: {e}")
            # Fallback: simple concat
            cmd_fallback = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file),
                '-c', 'copy',
                str(output_path)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
            return str(output_path)
    
    def _add_audio(self, video_path: str) -> str:
        """Add audio to the video"""
        output_path = self.output_path
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', self.audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-b:a', '192k',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error adding audio: {e}")
            raise
    
    def _cleanup(self):
        """Clean up temporary files"""
        import shutil
        
        try:
            if self.working_dir.exists():
                shutil.rmtree(self.working_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get information about a generated video"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # Extract relevant info
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
            
            return {
                'duration': float(info['format'].get('duration', 0)),
                'width': int(video_stream.get('width', 0)) if video_stream else 0,
                'height': int(video_stream.get('height', 0)) if video_stream else 0,
                'fps': eval(video_stream.get('r_frame_rate', '30/1')) if video_stream else 30,
                'video_codec': video_stream.get('codec_name', '') if video_stream else '',
                'audio_codec': audio_stream.get('codec_name', '') if audio_stream else '',
                'file_size': int(info['format'].get('size', 0))
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}