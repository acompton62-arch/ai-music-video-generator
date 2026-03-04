import re
from typing import List, Dict, Tuple

class LyricsParser:
    """Parses lyrics and creates timed segments for video generation"""
    
    def __init__(self, lyrics: str, duration: float):
        self.raw_lyrics = lyrics
        self.duration = duration
        self.segments = []
    
    def parse(self) -> List[Dict]:
        """Main parse method - handles various lyric formats"""
        # Detect format and parse accordingly
        if self._is_timed_lyrics():
            return self._parse_timed_lyrics()
        else:
            return self._parse_plain_lyrics()
    
    def _is_timed_lyrics(self) -> bool:
        """Check if lyrics contain timing information (LRC format)"""
        # LRC format: [mm:ss.xx]lyrics
        lrc_pattern = r'\[\d+:\d+[\.\d]*\]'
        return bool(re.search(lrc_pattern, self.raw_lyrics))
    
    def _parse_timed_lyrics(self) -> List[Dict]:
        """Parse LRC format lyrics with timestamps"""
        segments = []
        lines = self.raw_lyrics.strip().split('\n')
        
        for line in lines:
            # Match [mm:ss.xx] or [mm:ss:xx] format
            match = re.match(r'\[(\d+):(\d+)(?:[\.\:](\d+))?\](.*)', line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                milliseconds = int(match.group(3)) if match.group(3) else 0
                
                # Convert to seconds
                start_time = minutes * 60 + seconds + milliseconds / 100
                
                text = match.group(4).strip()
                
                if text:  # Skip empty lines
                    segments.append({
                        'text': text,
                        'start_time': start_time,
                        'end_time': None,  # Will be filled in later
                        'type': self._classify_line(text)
                    })
        
        # Fill in end times
        for i in range(len(segments) - 1):
            segments[i]['end_time'] = segments[i + 1]['start_time']
        
        # Last segment ends at song duration
        if segments:
            segments[-1]['end_time'] = self.duration
        
        return segments
    
    def _parse_plain_lyrics(self) -> List[Dict]:
        """Parse plain text lyrics and auto-distribute across duration"""
        segments = []
        
        # Split into lines
        lines = [line.strip() for line in self.raw_lyrics.strip().split('\n') if line.strip()]
        
        if not lines:
            return segments
        
        # Classify lines and structure
        structured_lines = []
        for i, line in enumerate(lines):
            structured_lines.append({
                'text': line,
                'type': self._classify_line(line),
                'word_count': len(line.split())
            })
        
        # Calculate time distribution
        total_words = sum(line['word_count'] for line in structured_lines)
        time_per_word = self.duration / max(total_words, 1)
        
        current_time = 0
        for line in structured_lines:
            # Calculate duration based on word count
            line_duration = line['word_count'] * time_per_word
            
            # Add small gaps between lines
            gap = min(0.5, line_duration * 0.1)
            
            segments.append({
                'text': line['text'],
                'start_time': round(current_time, 2),
                'end_time': round(current_time + line_duration - gap, 2),
                'type': line['type'],
                'word_count': line['word_count']
            })
            
            current_time += line_duration
        
        return segments
    
    def _classify_line(self, line: str) -> str:
        """Classify line type (verse, chorus, bridge, etc.)"""
        line_lower = line.lower().strip()
        
        # Check for explicit markers
        markers = {
            '[verse': 'verse',
            '[chorus': 'chorus',
            '[bridge': 'bridge',
            '[intro': 'intro',
            '[outro': 'outro',
            '[pre-chorus': 'pre-chorus',
            '[hook': 'hook'
        }
        
        for marker, line_type in markers.items():
            if line_lower.startswith(marker):
                return line_type
        
        # Heuristic classification
        # Repetitive lines might be chorus
        words = line.split()
        
        if len(words) <= 3:
            return 'short'
        elif any(word in line_lower for word in ['oh', 'ah', 'yeah', 'na', 'la', 'da']):
            return 'vocalization'
        
        return 'verse'
    
    def get_sections(self) -> List[Dict]:
        """Group segments into sections"""
        segments = self.parse()
        sections = []
        current_section = None
        
        for segment in segments:
            if current_section is None:
                current_section = {
                    'type': segment['type'],
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'lines': [segment['text']]
                }
            elif segment['type'] == current_section['type']:
                current_section['end_time'] = segment['end_time']
                current_section['lines'].append(segment['text'])
            else:
                sections.append(current_section)
                current_section = {
                    'type': segment['type'],
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'lines': [segment['text']]
                }
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def get_keywords(self) -> List[str]:
        """Extract significant keywords from lyrics for image generation"""
        import string
        
        # Common words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                      'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                      'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
                      'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                      'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'mine',
                      'yours', 'hers', 'ours', 'theirs', 'this', 'that', 'these', 'those',
                      'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how',
                      'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
                      'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                      'than', 'too', 'very', 'just', 'now', 'here', 'there', 'then',
                      'oh', 'ah', 'yeah', 'na', 'la', 'da', 'ooh', 'ahh'}
        
        # Clean and tokenize
        text = self.raw_lyrics.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        words = text.split()
        
        # Filter and count
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:20]]
    
    def get_mood_hints(self) -> Dict:
        """Analyze lyrics for mood/emotional content"""
        text = self.raw_lyrics.lower()
        
        # Define mood indicators
        mood_words = {
            'happy': ['happy', 'joy', 'smile', 'laugh', 'bright', 'sun', 'love', 'beautiful',
                      'wonderful', 'amazing', 'great', 'good', 'best', 'fun', 'dance', 'celebration'],
            'sad': ['sad', 'cry', 'tears', 'alone', 'lonely', 'dark', 'rain', 'pain', 'hurt',
                    'broken', 'lost', 'miss', 'gone', 'goodbye', 'leave', 'fall'],
            'romantic': ['love', 'heart', 'kiss', 'hold', 'together', 'forever', 'baby', 'darling',
                        'beautiful', 'eyes', 'touch', 'feel', 'dream'],
            'energetic': ['run', 'jump', 'fast', 'fire', 'wild', 'crazy', 'alive', 'power',
                         'strong', 'fight', 'win', 'rise', 'up', 'go'],
            'melancholic': ['memories', 'time', 'past', 'remember', 'used', 'once', 'fade',
                           'ghost', 'shadow', 'silence', 'quiet'],
            'hopeful': ['hope', 'dream', 'believe', 'future', 'tomorrow', 'shine', 'light',
                       'rise', 'new', 'begin', 'start', 'chance']
        }
        
        scores = {}
        for mood, words in mood_words.items():
            score = sum(1 for word in words if word in text)
            scores[mood] = score
        
        # Determine dominant mood
        dominant_mood = max(scores, key=scores.get) if max(scores.values()) > 0 else 'neutral'
        
        return {
            'dominant_mood': dominant_mood,
            'mood_scores': scores,
            'emotional_keywords': self._extract_emotional_words(text, mood_words)
        }
    
    def _extract_emotional_words(self, text: str, mood_words: Dict) -> List[str]:
        """Extract emotional words found in lyrics"""
        found = []
        for mood, words in mood_words.items():
            for word in words:
                if word in text and word not in found:
                    found.append(word)
        return found[:10]