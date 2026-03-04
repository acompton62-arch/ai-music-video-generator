from typing import List, Dict, Optional
import random

class ScenePlanner:
    """Plans visual scenes based on lyrics, audio analysis, and style preferences"""
    
    def __init__(self, segments: List[Dict], bpm: float, style: str = 'cinematic'):
        self.segments = segments
        self.bpm = bpm
        self.style = style
        self.scenes = []
        
        # Style definitions
        self.style_configs = {
            'cinematic': {
                'adjectives': ['cinematic', 'dramatic lighting', 'film grain', 'atmospheric', 'moody'],
                'color_palette': ['deep blues', 'golden hour', 'shadows', 'contrast'],
                'composition': ['wide angle', 'depth of field', 'rule of thirds']
            },
            'animated': {
                'adjectives': ['animated', 'colorful', 'vibrant', 'playful', 'cartoon style'],
                'color_palette': ['bright colors', 'pastels', 'neon accents'],
                'composition': ['dynamic', 'exaggerated perspective']
            },
            'abstract': {
                'adjectives': ['abstract', 'surreal', 'geometric', 'artistic', 'modern art'],
                'color_palette': ['bold contrasts', 'gradient blends', 'iridescent'],
                'composition': ['minimalist', 'symmetrical', 'fluid forms']
            },
            'nature': {
                'adjectives': ['nature photography', 'landscape', 'organic', 'natural', 'serene'],
                'color_palette': ['earth tones', 'greens', 'blues', 'warm sunlight'],
                'composition': ['panoramic', 'macro detail', 'environmental']
            },
            'urban': {
                'adjectives': ['urban', 'street photography', 'cityscape', 'gritty', 'modern'],
                'color_palette': ['neon lights', 'concrete grays', 'night city colors'],
                'composition': ['dutch angle', 'architecture focus', 'street level']
            },
            'fantasy': {
                'adjectives': ['fantasy art', 'magical', 'ethereal', 'enchanted', 'mystical'],
                'color_palette': ['mystical purples', 'glowing effects', 'starry night'],
                'composition': ['epic scale', 'magical elements', 'otherworldly']
            },
            'retro': {
                'adjectives': ['vintage', 'retro', '80s aesthetic', 'nostalgic', 'analog film'],
                'color_palette': ['warm vintage tones', 'film grain', 'faded colors'],
                'composition': ['classic portraiture', 'vintage framing']
            },
            'minimal': {
                'adjectives': ['minimal', 'clean', 'simple', 'elegant', 'modern'],
                'color_palette': ['neutral tones', 'black and white', 'subtle colors'],
                'composition': ['centered', 'negative space', 'geometric simplicity']
            }
        }
    
    def create_scenes(self) -> List[Dict]:
        """Create comprehensive scene plan"""
        if not self.segments:
            return []
        
        scenes = []
        total_segments = len(self.segments)
        
        # Extract themes and mood from lyrics
        keywords = self._extract_keywords()
        mood = self._analyze_mood()
        
        # Generate story arc
        story_arc = self._create_story_arc()
        
        for i, segment in enumerate(self.segments):
            # Determine scene position in narrative
            narrative_position = i / max(total_segments - 1, 1)
            
            # Create scene
            scene = {
                'segment_index': i,
                'text': segment['text'],
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'duration': segment['end_time'] - segment['start_time'],
                'segment_type': segment.get('type', 'verse'),
                
                # Visual properties
                'visual_prompt': self._generate_visual_prompt(
                    segment, keywords, mood, narrative_position, story_arc
                ),
                'camera_movement': self._suggest_camera_movement(narrative_position, segment),
                'transition_in': self._suggest_transition(i, narrative_position),
                'transition_out': 'fade' if i == total_segments - 1 else 'crossfade',
                
                # Animation parameters
                'animation_speed': self._calculate_animation_speed(segment),
                'parallax_layers': self._suggest_parallax(narrative_position),
                
                # Text overlay settings
                'text_position': self._suggest_text_position(i),
                'text_animation': self._suggest_text_animation(segment),
                
                # Effects
                'effects': self._suggest_effects(narrative_position, mood)
            }
            
            scenes.append(scene)
        
        return scenes
    
    def _extract_keywords(self) -> List[str]:
        """Extract significant keywords from segments"""
        all_text = ' '.join([s['text'] for s in self.segments])
        words = all_text.lower().split()
        
        # Simple keyword extraction
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                      'i', 'you', 'we', 'they', 'it', 'me', 'my', 'your', 'our', 'us'}
        
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count and return top keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, _ in word_counts.most_common(10)]
    
    def _analyze_mood(self) -> str:
        """Analyze overall mood from lyrics"""
        all_text = ' '.join([s['text'] for s in self.segments]).lower()
        
        mood_indicators = {
            'uplifting': ['happy', 'joy', 'love', 'light', 'shine', 'bright', 'rise', 'hope'],
            'melancholic': ['sad', 'cry', 'alone', 'dark', 'lost', 'gone', 'rain', 'pain'],
            'energetic': ['fire', 'run', 'jump', 'fast', 'wild', 'alive', 'power', 'strong'],
            'romantic': ['love', 'heart', 'kiss', 'hold', 'together', 'forever', 'beautiful'],
            'introspective': ['think', 'wonder', 'dream', 'time', 'memories', 'past', 'silence']
        }
        
        scores = {}
        for mood, words in mood_indicators.items():
            scores[mood] = sum(1 for word in words if word in all_text)
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'neutral'
    
    def _create_story_arc(self) -> Dict:
        """Create a narrative story arc for the video"""
        return {
            'introduction': {'range': (0, 0.15), 'energy': 0.3, 'style_modifier': 'establishing shot'},
            'rising_action': {'range': (0.15, 0.5), 'energy': 0.6, 'style_modifier': 'building tension'},
            'climax': {'range': (0.5, 0.75), 'energy': 1.0, 'style_modifier': 'peak emotional moment'},
            'falling_action': {'range': (0.75, 0.9), 'energy': 0.5, 'style_modifier': 'resolution'},
            'conclusion': {'range': (0.9, 1.0), 'energy': 0.2, 'style_modifier': 'fade out'}
        }
    
    def _generate_visual_prompt(self, segment: Dict, keywords: List[str], 
                                  mood: str, position: float, story_arc: Dict) -> str:
        """Generate a detailed visual prompt for AI image generation"""
        
        # Get style configuration
        style_config = self.style_configs.get(self.style, self.style_configs['cinematic'])
        
        # Determine story phase
        story_phase = 'rising_action'
        for phase, config in story_arc.items():
            if config['range'][0] <= position <= config['range'][1]:
                story_phase = phase
                break
        
        arc_config = story_arc[story_phase]
        
        # Build prompt components
        components = []
        
        # Subject matter from lyrics
        subject = self._interpret_lyrics_visually(segment['text'], keywords, mood)
        components.append(subject)
        
        # Style adjectives
        adjectives = random.sample(style_config['adjectives'], min(3, len(style_config['adjectives'])))
        components.append(', '.join(adjectives))
        
        # Mood and atmosphere
        components.append(f'{mood} atmosphere')
        
        # Story phase modifier
        components.append(arc_config['style_modifier'])
        
        # Color palette
        colors = random.sample(style_config['color_palette'], min(2, len(style_config['color_palette'])))
        components.append(', '.join(colors))
        
        # Composition
        composition = random.choice(style_config['composition'])
        components.append(composition)
        
        # Technical quality indicators
        components.append('high quality, detailed, 4K, professional')
        
        # Join all components
        prompt = ', '.join(components)
        
        return prompt
    
    def _interpret_lyrics_visually(self, text: str, keywords: List[str], mood: str) -> str:
        """Convert lyrics into visual concepts"""
        text_lower = text.lower()
        
        # Visual metaphor mappings
        visual_mappings = {
            # Nature elements
            'sun': 'golden sun rays breaking through clouds',
            'moon': 'luminous moon in starlit sky',
            'rain': 'rain droplets on window, moody atmosphere',
            'ocean': 'vast ocean waves, horizon view',
            'sky': 'dramatic sky with clouds',
            'fire': 'warm flames dancing, dramatic lighting',
            'forest': 'mystical forest with light filtering through trees',
            'mountain': 'majestic mountain peaks at golden hour',
            
            # Emotions/concepts
            'love': 'intertwined silhouettes, warm embrace, romantic lighting',
            'heart': 'abstract heart symbol, glowing warmly',
            'dream': 'surreal dreamscape, floating elements',
            'memory': 'vintage photograph aesthetic, nostalgic tones',
            'time': 'flowing hourglass or clock, symbolic representation',
            'hope': 'light breaking through darkness, horizon glow',
            'pain': 'abstract representation of struggle, dramatic shadows',
            
            # Actions
            'run': 'dynamic motion blur, movement captured',
            'dance': 'graceful dance movement, flowing fabric',
            'fly': 'soaring through sky, sense of freedom',
            
            # Places
            'city': 'urban cityscape, lights at night',
            'home': 'cozy interior, warm lighting',
            'road': 'endless road stretching into distance',
            'night': 'night scene, stars and moonlight',
            
            # Abstract
            'light': 'dramatic lighting effects, rays and beams',
            'dark': 'shadows and contrast, mysterious atmosphere',
            'alone': 'solitary figure in vast space',
            'together': 'unified elements, connection visual'
        }
        
        # Check for specific visual elements
        for keyword, visual in visual_mappings.items():
            if keyword in text_lower:
                return visual
        
        # Generate based on mood
        mood_visuals = {
            'uplifting': 'bright landscape with hopeful elements, ascending perspective',
            'melancholic': 'misty scene with soft focus, emotional depth',
            'energetic': 'dynamic composition with vibrant energy, motion',
            'romantic': 'intimate scene with warm tones, soft focus',
            'introspective': 'thoughtful composition with symbolic elements',
            'neutral': f'artistic interpretation of "{text[:30]}..." concept'
        }
        
        return mood_visuals.get(mood, mood_visuals['neutral'])
    
    def _suggest_camera_movement(self, position: float, segment: Dict) -> str:
        """Suggest camera movement for the scene"""
        # More dynamic movements during climax
        if 0.5 <= position <= 0.75:
            return random.choice(['push in', 'dramatic zoom', 'dynamic pan', 'orbit'])
        elif position < 0.15:
            return random.choice(['establishing shot', 'slow reveal', 'wide pan'])
        elif position > 0.9:
            return random.choice(['slow pull back', 'fade to wide', 'gentle zoom out'])
        else:
            return random.choice(['slow push', 'gentle pan', 'subtle drift'])
    
    def _suggest_transition(self, scene_index: int, position: float) -> str:
        """Suggest transition type for scene entrance"""
        if scene_index == 0:
            return 'fade_in'
        elif position >= 0.5 and position <= 0.75:
            return random.choice(['quick cut', 'flash transition', 'dynamic wipe'])
        else:
            return random.choice(['crossfade', 'smooth dissolve', 'fade'])
    
    def _calculate_animation_speed(self, segment: Dict) -> float:
        """Calculate appropriate animation speed based on BPM and segment"""
        base_speed = self.bpm / 120.0  # Normalize to 120 BPM
        
        # Adjust based on segment type
        type_multipliers = {
            'verse': 0.8,
            'chorus': 1.2,
            'bridge': 0.6,
            'intro': 0.5,
            'outro': 0.5,
            'vocalization': 0.7
        }
        
        multiplier = type_multipliers.get(segment.get('type', 'verse'), 1.0)
        
        return min(max(base_speed * multiplier, 0.3), 2.0)  # Clamp between 0.3 and 2.0
    
    def _suggest_parallax(self, position: float) -> List[Dict]:
        """Suggest parallax layer structure for depth"""
        layers = []
        
        # Background layer always present
        layers.append({
            'depth': 1.0,
            'movement': 'slow drift opposite direction',
            'elements': 'atmospheric elements, sky, distant objects'
        })
        
        # Add more layers during more intense moments
        if position > 0.3:
            layers.append({
                'depth': 0.5,
                'movement': 'medium speed parallax',
                'elements': 'mid-ground elements'
            })
        
        if position > 0.5:
            layers.append({
                'depth': 0.2,
                'movement': 'subtle movement',
                'elements': 'foreground elements, particles'
            })
        
        return layers
    
    def _suggest_text_position(self, scene_index: int) -> Dict:
        """Suggest text overlay position"""
        positions = [
            {'x': 'center', 'y': '85%'},  # Bottom center
            {'x': 'center', 'y': '15%'},  # Top center
            {'x': 'center', 'y': 'center'},  # Center
            {'x': '10%', 'y': 'center'},  # Left
            {'x': '90%', 'y': 'center'}   # Right
        ]
        
        # Vary position to keep visual interest
        return positions[scene_index % len(positions)]
    
    def _suggest_text_animation(self, segment: Dict) -> str:
        """Suggest text animation style"""
        duration = segment['end_time'] - segment['start_time']
        
        if duration < 2:
            return 'quick_fade'
        elif duration < 4:
            return 'typewriter'
        else:
            return 'fade_in_hold'
    
    def _suggest_effects(self, position: float, mood: str) -> List[str]:
        """Suggest visual effects based on position and mood"""
        effects = []
        
        # Base effects
        effects.append('color_grading')
        
        # Position-based effects
        if 0.45 <= position <= 0.55:  # Pre-climax
            effects.append('intensifying_brightness')
        elif 0.5 <= position <= 0.75:  # Climax
            effects.extend(['dynamic_particles', 'light_rays'])
        
        # Mood-based effects
        mood_effects = {
            'uplifting': ['warm_tones', 'lens_flare'],
            'melancholic': ['cool_tones', 'vignette'],
            'energetic': ['sharpen', 'vibrance_boost'],
            'romantic': ['soft_focus', 'warm_glow'],
            'introspective': ['subtle_grain', 'faded_colors']
        }
        
        if mood in mood_effects:
            effects.extend(mood_effects[mood][:1])  # Add one mood effect
        
        return effects
    
    def get_scene_summary(self) -> Dict:
        """Get summary of the planned scenes"""
        scenes = self.create_scenes()
        
        return {
            'total_scenes': len(scenes),
            'total_duration': sum(s['duration'] for s in scenes),
            'style': self.style,
            'dominant_mood': self._analyze_mood(),
            'average_scene_duration': sum(s['duration'] for s in scenes) / len(scenes) if scenes else 0,
            'keywords_used': self._extract_keywords()
        }