# Calendar Generator

Generate beautiful A3 calendars with custom images and titles for any year. The calendars are in Spanish and include special dates like birthdays and holidays.

## Features

- Generate calendars for any year
- Custom images for each month
- Customizable titles for each month's image
- Special dates support (birthdays, holidays)
- A3 format (297mm × 420mm)
- High-quality image handling

## Requirements

- Python 3.x
- Pillow (PIL) library
- DejaVu Sans font

## Directory Structure

```
cal2025/
├── generate_calendars.py   # Main script
├── imagenes_ejemplo/      # Default example images
├── pics/                  # Year-specific images
│   └── YYYY/             # Replace YYYY with year
│       ├── Enero.jpg
│       ├── Febrero.tif
│       └── titles.txt    # Optional custom titles
└── calendarios_YYYY/     # Generated calendars
```

## Usage

1. Generate calendars for a specific year:
   ```bash
   python3 generate_calendars.py YYYY
   ```
   Replace YYYY with the desired year (e.g., 2025)

2. Custom Images:
   - Create a directory for your year: `pics/YYYY/`
   - Add your images with Spanish month names (e.g., Enero.jpg, Febrero.tif, Marzo.webp).
   - Image requirements:
     - Supported Formats: JPG, TIF, PNG, WebP
     - Transparency: PNG/WebP transparency is automatically handled with a white background.
     - Aspect ratio: 3:2 (landscape) recommended
     - Resolution: Maximum quality recommended for A3 printing

3. Custom Titles (Optional):
   - Create `pics/YYYY/titles.txt`
   - Add 12 lines, one title per month
   - If not provided, default titles will be used

## Page Configuration

- Paper size: A3 (297mm × 420mm)
- Picture area: 280mm × 200mm (centered at top)
- Calendar area: 280mm × 160mm (centered below picture)

## Special Dates

The calendar includes:
- Birthdays
- Christmas (December 25)
- New Year's Day (January 1)

## Examples

The repository includes:
- Example images in `imagenes_ejemplo/`
- Generated calendars for 2025-2027
- Example titles file for 2025 with Spanish locations

## Resources

- [Notion Project Page](https://www.notion.so/xgpo/Calendars-ddffe2a9a7d846968ea93833bef50f59)
- [Spanish Calendar Reference](https://www.calendarioslaborales.com/calendario-laboral-madrid-2025.htm)
- [GitHub Repository](https://github.com/xalvagp/cal2025)

## Contributing

Feel free to submit issues and enhancement requests!
