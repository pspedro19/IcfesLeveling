"""
Placeholder Image Generator for ICFES Leveling System
Creates subject-specific placeholder images for missing media files
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class PlaceholderGenerator:
    """Generates placeholder images for different subjects and types"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subject configurations
        self.subjects_config = {
            'matematicas': {
                'color': '#2196F3',  # Blue
                'icon': '∑∫∆',
                'name': 'Matemáticas'
            },
            'lectura_critica': {
                'color': '#4CAF50',  # Green
                'icon': '📖',
                'name': 'Lectura Crítica'
            },
            'ciencias_naturales': {
                'color': '#FF9800',  # Orange
                'icon': '⚗️🔬',
                'name': 'Ciencias Naturales'
            },
            'ciencias_sociales': {
                'color': '#9C27B0',  # Purple
                'icon': '🌍',
                'name': 'Ciencias Sociales'
            },
            'ingles': {
                'color': '#F44336',  # Red
                'icon': '🇺🇸',
                'name': 'Inglés'
            },
            'general': {
                'color': '#607D8B',  # Blue Grey
                'icon': '📝',
                'name': 'General'
            }
        }
        
        # Image type configurations
        self.image_types = {
            'question': {
                'size': (400, 300),
                'text': 'Pregunta\nno disponible'
            },
            'option_a': {
                'size': (200, 150),
                'text': 'Opción A\nno disponible'
            },
            'option_b': {
                'size': (200, 150),
                'text': 'Opción B\nno disponible'
            },
            'option_c': {
                'size': (200, 150),
                'text': 'Opción C\nno disponible'
            },
            'option_d': {
                'size': (200, 150),
                'text': 'Opción D\nno disponible'
            },
            'generic': {
                'size': (300, 200),
                'text': 'Imagen\nno disponible'
            }
        }
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def darken_color(self, rgb: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
        """Darken an RGB color"""
        return tuple(int(c * factor) for c in rgb)
    
    def get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get font with fallback options"""
        font_paths = [
            "arial.ttf",
            "Arial.ttf",
            "/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        
        # Fallback to default font
        return ImageFont.load_default()
    
    def create_placeholder(
        self,
        subject: str,
        image_type: str,
        width: int,
        height: int,
        text: str
    ) -> Image.Image:
        """Create a placeholder image for specific subject and type"""
        
        subject_config = self.subjects_config.get(subject, self.subjects_config['general'])
        base_color = self.hex_to_rgb(subject_config['color'])
        dark_color = self.darken_color(base_color)
        
        # Create image with gradient background
        img = Image.new('RGB', (width, height), base_color)
        draw = ImageDraw.Draw(img)
        
        # Create subtle gradient effect
        for i in range(height):
            alpha = i / height
            color_r = int(base_color[0] * (1 - alpha) + dark_color[0] * alpha)
            color_g = int(base_color[1] * (1 - alpha) + dark_color[1] * alpha)
            color_b = int(base_color[2] * (1 - alpha) + dark_color[2] * alpha)
            draw.line([(0, i), (width, i)], fill=(color_r, color_g, color_b))
        
        # Add border
        border_color = self.darken_color(base_color, 0.5)
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=2)
        
        # Add subject icon (if supported)
        icon_text = subject_config['icon']
        if icon_text and not any(ord(char) > 127 for char in icon_text if char not in '⚗️🔬📖🌍🇺🇸📝'):
            try:
                icon_font = self.get_font(min(width, height) // 8)
                icon_bbox = draw.textbbox((0, 0), icon_text, font=icon_font)
                icon_width = icon_bbox[2] - icon_bbox[0]
                icon_height = icon_bbox[3] - icon_bbox[1]
                
                icon_x = (width - icon_width) // 2
                icon_y = height // 6
                
                # Add shadow for icon
                draw.text((icon_x + 2, icon_y + 2), icon_text, fill=(0, 0, 0, 80), font=icon_font)
                draw.text((icon_x, icon_y), icon_text, fill='white', font=icon_font)
            except Exception:
                pass  # Skip icon if it fails
        
        # Add main text
        main_font = self.get_font(min(width, height) // 12)
        lines = text.split('\n')
        
        total_height = 0
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=main_font)
            line_height = bbox[3] - bbox[1]
            line_heights.append(line_height)
            total_height += line_height
        
        # Center text vertically
        start_y = (height - total_height) // 2 + height // 8
        
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=main_font)
            line_width = bbox[2] - bbox[0]
            line_x = (width - line_width) // 2
            line_y = start_y + sum(line_heights[:i])
            
            # Add text shadow
            draw.text((line_x + 1, line_y + 1), line, fill=(0, 0, 0, 100), font=main_font)
            draw.text((line_x, line_y), line, fill='white', font=main_font)
        
        # Add subject name at bottom
        subject_name = subject_config['name']
        subject_font = self.get_font(min(width, height) // 16)
        subject_bbox = draw.textbbox((0, 0), subject_name, font=subject_font)
        subject_width = subject_bbox[2] - subject_bbox[0]
        subject_x = (width - subject_width) // 2
        subject_y = height - height // 8
        
        # Add subtle background for subject name
        padding = 5
        draw.rectangle([
            subject_x - padding,
            subject_y - padding,
            subject_x + subject_width + padding,
            subject_y + subject_bbox[3] - subject_bbox[1] + padding
        ], fill=(*dark_color, 120))
        
        draw.text((subject_x, subject_y), subject_name, fill='white', font=subject_font)
        
        return img
    
    def generate_all_placeholders(self) -> List[str]:
        """Generate all placeholder combinations"""
        generated_files = []
        
        for subject, subject_config in self.subjects_config.items():
            for image_type, type_config in self.image_types.items():
                # Create placeholder
                img = self.create_placeholder(
                    subject=subject,
                    image_type=image_type,
                    width=type_config['size'][0],
                    height=type_config['size'][1],
                    text=type_config['text']
                )
                
                # Save placeholder
                filename = f"{subject}_{image_type}_placeholder.png"
                filepath = self.output_dir / filename
                
                img.save(filepath, 'PNG', optimize=True)
                generated_files.append(str(filepath))
                logger.info(f"Generated placeholder: {filename}")
        
        return generated_files
    
    def create_readme(self) -> str:
        """Create README file explaining the placeholders"""
        readme_content = """# Placeholder Images

This directory contains automatically generated placeholder images for the ICFES Leveling system.

## Structure

Placeholders are named using the pattern: `{subject}_{image_type}_placeholder.png`

### Subjects:
- `matematicas`: Matemáticas (Blue theme)
- `lectura_critica`: Lectura Crítica (Green theme)  
- `ciencias_naturales`: Ciencias Naturales (Orange theme)
- `ciencias_sociales`: Ciencias Sociales (Purple theme)
- `ingles`: Inglés (Red theme)
- `general`: General/Default (Grey theme)

### Image Types:
- `question`: Main question images (400x300)
- `option_a`: Option A images (200x150)
- `option_b`: Option B images (200x150)
- `option_c`: Option C images (200x150)
- `option_d`: Option D images (200x150)
- `generic`: Generic fallback images (300x200)

## Usage

These placeholders are automatically served when:
1. A requested image file doesn't exist
2. A file path cannot be resolved
3. A file fails validation

## Regeneration

To regenerate these placeholders, run:
```python
from app.scripts.create_placeholders import PlaceholderGenerator
generator = PlaceholderGenerator("path/to/placeholders")
generator.generate_all_placeholders()
```

Generated on: """ + str(datetime.now()) + """
"""
        
        readme_path = self.output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        return str(readme_path)

def main():
    """Main function to generate placeholders"""
    
    # Determine output directory
    script_dir = Path(__file__).parent
    backend_root = script_dir.parent.parent
    placeholders_dir = backend_root.parent.parent / "database" / "allquestions" / "placeholders"
    
    logger.info(f"Generating placeholders in: {placeholders_dir}")
    
    # Create generator and generate all placeholders
    generator = PlaceholderGenerator(str(placeholders_dir))
    generated_files = generator.generate_all_placeholders()
    
    # Create README
    readme_path = generator.create_readme()
    
    logger.info(f"Generated {len(generated_files)} placeholder images")
    logger.info(f"Created README at: {readme_path}")
    
    return generated_files

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()