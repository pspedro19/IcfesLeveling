# Placeholder Images

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

Generated on: 2025-09-08 22:16:50.553897
