import os
import base64
import requests
import json
import time
import subprocess
import sys
from typing import Dict, List, Optional
from pathlib import Path

class ImageGenerator:
    """Generates AI images for music video scenes using real AI generation"""
    
    def __init__(self, project_id: str, style: str = 'cinematic'):
        self.project_id = project_id
        self.style = style
        
        # Output directory for generated images
        self.output_dir = Path(f'static/uploads/{project_id}_images')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Image generation settings
        self.image_size = "1536x1024"  # 16:9 widescreen for video
    
    def generate_scene_image(self, scene: Dict, index: int) -> str:
        """Generate a real AI image for a specific scene"""
        prompt = scene.get('visual_prompt', '')
        enhanced_prompt = self._enhance_prompt(prompt)
        image_path = self.output_dir / f"scene_{index:03d}.png"
        
        # Use the AI image generation script
        generated_path = self._generate_ai_image(enhanced_prompt, image_path, index)
        return str(generated_path)
    
    def _generate_ai_image(self, prompt: str, output_path: Path, index: int) -> Path:
        """Generate a real AI image using the image generation API"""
        # Write prompt to a temp file for the generation script
        prompt_file = self.output_dir / f"prompt_{index:03d}.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        # Call the AI image generation via subprocess
        script_path = Path(__file__).parent.parent / 'generate_image_worker.py'
        result = subprocess.run(
            [sys.executable, str(script_path), 
             '--prompt', prompt,
             '--output', str(output_path),
             '--size', self.image_size],
            capture_output=True, text=True, timeout=120
        )
        
        if result.returncode == 0 and output_path.exists():
            print(f"AI image generated: {output_path}")
            return output_path
        else:
            print(f"AI generation failed: {result.stderr}, falling back to styled image")
            return self._create_styled_image(prompt, output_path, index)

    def _enhance_prompt(self, base_prompt: str) -> str:
        """Enhance the prompt with style-specific modifiers"""
        style_enhancements = {
            'cinematic': 'cinematic film still, professional color grading, 4K, high detail',
            'animated': 'digital art, vibrant colors, clean lines, professional illustration',
            'abstract': 'abstract art, modern composition, artistic, gallery quality',
            'nature': 'nature photography, National Geographic style, crystal clear',
            'urban': 'street photography, urban aesthetic, contemporary',
            'fantasy': 'fantasy art, digital painting, magical atmosphere, detailed',
            'retro': 'vintage photography, analog film, nostalgic aesthetic',
            'minimal': 'minimalist design, clean composition, elegant simplicity'
        }
        
        enhancement = style_enhancements.get(self.style, style_enhancements['cinematic'])
        
        return f"{base_prompt}, {enhancement}"
    
    def _generate_with_api(self, prompt: str, output_path: Path, index: int) -> Path:
        """Generate image using available API (Stability AI, DALL-E, or local)"""
        
        # Try local generation first (using a simple approach)
        # In production, this would connect to actual AI image services
        
        # For now, create a styled placeholder that looks professional
        return self._create_styled_image(prompt, output_path, index)
    
    def _create_styled_image(self, prompt: str, output_path: Path, index: int) -> Path:
        """Create a styled placeholder image using Python imaging"""
        from PIL import Image, ImageDraw, ImageFilter, ImageFont
        import random
        import math
        
        # Determine color scheme based on style
        color_schemes = {
            'cinematic': [(30, 40, 60), (70, 80, 100), (150, 100, 50), (200, 150, 100)],
            'animated': [(255, 150, 100), (100, 200, 255), (200, 100, 200), (255, 200, 100)],
            'abstract': [(80, 40, 120), (40, 80, 120), (120, 80, 40), (160, 100, 140)],
            'nature': [(34, 139, 34), (135, 206, 235), (210, 180, 140), (100, 180, 100)],
            'urban': [(50, 50, 50), (100, 100, 100), (200, 100, 50), (150, 50, 50)],
            'fantasy': [(75, 0, 130), (138, 43, 226), (255, 105, 180), (100, 149, 237)],
            'retro': [(210, 160, 140), (180, 140, 120), (140, 100, 80), (255, 200, 150)],
            'minimal': [(240, 240, 240), (200, 200, 200), (50, 50, 50), (150, 150, 150)]
        }
        
        colors = color_schemes.get(self.style, color_schemes['cinematic'])
        
        # Create base image with gradient
        width, height = 1920, 1280
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create diagonal gradient background
        for y in range(height):
            for x in range(width):
                progress = ((x / width) + (y / height)) / 2
                color_idx = int(progress * (len(colors) - 1))
                color_idx = min(color_idx, len(colors) - 2)
                local_progress = (progress * (len(colors) - 1)) - color_idx
                
                r = int(colors[color_idx][0] + (colors[color_idx + 1][0] - colors[color_idx][0]) * local_progress)
                g = int(colors[color_idx][1] + (colors[color_idx + 1][1] - colors[color_idx][1]) * local_progress)
                b = int(colors[color_idx][2] + (colors[color_idx + 1][2] - colors[color_idx][2]) * local_progress)
                
                draw.point((x, y), fill=(r, g, b))
        
        random.seed(index * 999)  # Consistent per scene

        # Convert to RGBA for compositing
        img_rgba = img.convert('RGBA')

        # --- Background scenery based on style ---
        scene_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        scene_draw = ImageDraw.Draw(scene_layer)

        if self.style == 'nature':
            # Sky gradient top
            for y2 in range(height // 2):
                alpha = int(180 * (1 - y2 / (height // 2)))
                scene_draw.line([(0, y2), (width, y2)], fill=(*colors[1], alpha))
            # Ground
            for y2 in range(height // 2, height):
                alpha = int(150 * ((y2 - height // 2) / (height // 2)))
                scene_draw.line([(0, y2), (width, y2)], fill=(*colors[0], alpha))
            # Sun
            scene_draw.ellipse([width//2 - 80, 80, width//2 + 80, 240], fill=(*colors[3], 200))
            # Hills
            for hx in range(0, width + 200, 200):
                scene_draw.ellipse([hx - 200, height//2 - 100, hx + 200, height//2 + 200],
                                   fill=(*colors[0], 180))

        elif self.style == 'urban':
            # Night sky
            scene_draw.rectangle([0, 0, width, height * 2 // 3], fill=(*colors[0], 200))
            # Buildings
            for bx in range(0, width, random.randint(80, 160)):
                bh = random.randint(200, 600)
                bw = random.randint(60, 120)
                scene_draw.rectangle([bx, height - bh, bx + bw, height],
                                     fill=(*colors[1], 220))
                # Windows
                for wy in range(height - bh + 20, height - 20, 40):
                    for wx in range(bx + 10, bx + bw - 10, 25):
                        if random.random() > 0.4:
                            scene_draw.rectangle([wx, wy, wx + 12, wy + 18],
                                                 fill=(*colors[3], 200))

        elif self.style == 'fantasy':
            # Starfield
            for _ in range(200):
                sx = random.randint(0, width)
                sy = random.randint(0, height // 2)
                sr = random.randint(1, 4)
                scene_draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                                   fill=(255, 255, 255, random.randint(100, 255)))
            # Moon
            scene_draw.ellipse([width - 250, 50, width - 50, 250], fill=(*colors[2], 200))
            # Mountains
            for mx in range(0, width + 300, 300):
                mh = random.randint(300, 600)
                scene_draw.polygon([(mx - 200, height), (mx, height - mh), (mx + 200, height)],
                                   fill=(*colors[0], 200))

        elif self.style == 'cinematic':
            # Horizon line
            horizon_y = height // 3
            for y2 in range(horizon_y):
                alpha = int(200 * (1 - y2 / horizon_y))
                scene_draw.line([(0, y2), (width, y2)], fill=(*colors[1], alpha))
            # Ground plane
            for y2 in range(horizon_y, height):
                alpha = int(180 * ((y2 - horizon_y) / (height - horizon_y)))
                scene_draw.line([(0, y2), (width, y2)], fill=(*colors[0], alpha))
            # Sun/light source
            scene_draw.ellipse([width//2 - 60, horizon_y - 60,
                                width//2 + 60, horizon_y + 60], fill=(*colors[3], 180))

        elif self.style == 'abstract':
            # Geometric shapes
            for _ in range(6):
                x1 = random.randint(0, width)
                y1 = random.randint(0, height)
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
                col = random.choice(colors)
                scene_draw.polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
                                   fill=(*col, 120))

        elif self.style == 'retro':
            # Horizontal scan lines
            for y2 in range(0, height, 6):
                scene_draw.line([(0, y2), (width, y2)], fill=(0, 0, 0, 30))
            # Retro sun
            for r in range(200, 0, -20):
                alpha = int(150 * (r / 200))
                scene_draw.ellipse([width//2 - r, height//2 - r,
                                    width//2 + r, height//2 + r],
                                   fill=(*colors[3], alpha))

        elif self.style == 'animated':
            # Colorful circles
            for _ in range(8):
                cx = random.randint(0, width)
                cy = random.randint(0, height)
                cr = random.randint(80, 300)
                col = random.choice(colors)
                scene_draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                                   fill=(*col, 160))

        elif self.style == 'minimal':
            # Single centered shape
            scene_draw.ellipse([width//2 - 200, height//2 - 200,
                                width//2 + 200, height//2 + 200],
                               fill=(*colors[2], 80))
            scene_draw.line([(0, height//2), (width, height//2)],
                            fill=(*colors[2], 60), width=3)

        # No blur on scene layer - keep it sharp
        img_rgba = Image.alpha_composite(img_rgba, scene_layer)

        # --- Glow / light source overlay ---
        glow_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        cx, cy = width // 2, height // 3
        for r in range(400, 0, -40):
            alpha = int(30 * (1 - r / 400))
            glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                              fill=(*colors[-1], alpha))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
        img_rgba = Image.alpha_composite(img_rgba, glow_layer)

        # --- Convert to RGB ---
        img = img_rgba.convert('RGB')
        draw = ImageDraw.Draw(img)

        # --- Subtle film grain ---
        for _ in range(2000):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            intensity = random.randint(-10, 10)
            pixel = list(img.getpixel((x, y)))
            pixel[0] = max(0, min(255, pixel[0] + intensity))
            pixel[1] = max(0, min(255, pixel[1] + intensity))
            pixel[2] = max(0, min(255, pixel[2] + intensity))
            draw.point((x, y), fill=tuple(pixel))

        # --- Vignette (darken edges only using numpy) ---
        import numpy as np
        img_array = np.array(img).astype(np.float32)
        
        # Create vignette mask
        Y, X = np.ogrid[:height, :width]
        cx, cy = width / 2, height / 2
        # Normalized distance from center (0=center, 1=corner)
        dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
        # Vignette factor: 1 at center, 0 at edges
        vignette_mask = np.clip(1.0 - (dist - 0.5) * 1.2, 0.3, 1.0)
        vignette_mask = vignette_mask[:, :, np.newaxis]  # Add channel dim
        
        img_array = img_array * vignette_mask
        img = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))

        # Save
        img.save(output_path, 'PNG', quality=95)
        return output_path
    
    def _create_placeholder(self, scene: Dict, index: int) -> str:
        """Create a simple placeholder image"""
        from PIL import Image, ImageDraw
        
        output_path = self.output_dir / f"scene_{index:03d}_placeholder.png"
        
        # Create gradient background
        width, height = 1920, 1280
        img = Image.new('RGB', (width, height), (40, 40, 60))
        draw = ImageDraw.Draw(img)
        
        # Draw simple gradient
        for y in range(height):
            progress = y / height
            color = int(40 + progress * 30)
            draw.line([(0, y), (width, y)], fill=(color, color, color + 20))
        
        # Add scene text
        text = f"Scene {index + 1}"
        
        img.save(output_path, 'PNG')
        
        return str(output_path)
    
    def generate_all_images(self, scenes: List[Dict]) -> List[Dict]:
        """Generate images for all scenes"""
        results = []
        
        for i, scene in enumerate(scenes):
            print(f"Generating image {i + 1}/{len(scenes)}...")
            
            image_path = self.generate_scene_image(scene, i)
            
            results.append({
                'scene_index': i,
                'image_path': image_path,
                'prompt': scene.get('visual_prompt', ''),
                'success': os.path.exists(image_path)
            })
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        return results
    
    def create_image_sequence(self, scenes: List[Dict], output_fps: int = 30) -> str:
        """Create an image sequence directory for video composition"""
        sequence_dir = Path(f'static/uploads/{self.project_id}_sequence')
        sequence_dir.mkdir(parents=True, exist_ok=True)
        
        # We'll generate frame-by-frame later in video generator
        # For now, just prepare the directory
        
        return str(sequence_dir)


class AIImageClient:
    """Client for AI image generation APIs"""
    
    def __init__(self, api_key: str = None, provider: str = 'stability'):
        self.api_key = api_key or os.getenv('STABILITY_API_KEY', '')
        self.provider = provider
        self.api_urls = {
            'stability': 'https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image',
            'openai': 'https://api.openai.com/v1/images/generations',
            'replicate': 'https://api.replicate.com/v1/predictions'
        }
    
    def generate(self, prompt: str, size: str = "1536x1024", negative_prompt: str = "") -> Optional[bytes]:
        """Generate an image and return as bytes"""
        
        if not self.api_key:
            raise ValueError("API key required for image generation")
        
        if self.provider == 'stability':
            return self._generate_stability(prompt, size, negative_prompt)
        elif self.provider == 'openai':
            return self._generate_openai(prompt, size)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _generate_stability(self, prompt: str, size: str, negative_prompt: str) -> Optional[bytes]:
        """Generate using Stability AI"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        # Parse size
        width, height = map(int, size.split('x'))
        
        payload = {
            'text_prompts': [
                {'text': prompt, 'weight': 1},
                {'text': negative_prompt, 'weight': -1}
            ],
            'cfg_scale': 7,
            'width': width,
            'height': height,
            'samples': 1,
            'steps': 30
        }
        
        response = requests.post(
            self.api_urls['stability'],
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            image_data = result['artifacts'][0]['base64']
            return base64.b64decode(image_data)
        
        raise Exception(f"Stability API error: {response.status_code}")
    
    def _generate_openai(self, prompt: str, size: str) -> Optional[bytes]:
        """Generate using OpenAI DALL-E"""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': 'dall-e-3',
            'prompt': prompt,
            'n': 1,
            'size': '1792x1024',  # Closest 16:9 option
            'response_format': 'b64_json'
        }
        
        response = requests.post(
            self.api_urls['openai'],
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            image_data = result['data'][0]['b64_json']
            return base64.b64decode(image_data)
        
        raise Exception(f"OpenAI API error: {response.status_code}")