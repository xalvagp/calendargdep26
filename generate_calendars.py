from PIL import Image, ImageDraw, ImageFont
import calendar
from datetime import datetime, date, timedelta
import os
import argparse

# Spanish day and month names
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Default titles for each month
DEFAULT_TITLES = ['Retiro', 'Tarraco', 'Tarraco', 'Acueducto de Tarraco', 
                 'Sardignia', 'Tarraco', 'Retiro', 'Sardignia', 
                 'La Araña', 'Retiro', 'Farmacia', 'Sardignia']

# Special days with their month, day, and description
SPECIAL_DAYS = [
    {'month': 6, 'day': 24, 'title': 'Marta', 'image': 'mdp.jpg'},
    {'month': 5, 'day': 26, 'title': 'Salva', 'image': 'sgp.jpg'},
    {'month': 2, 'day': 10, 'title': 'Naná', 'image': 'agp.jpg'},
    {'month': 11, 'day': 23, 'title': 'Clara', 'image': 'cgp.jpg'},
    {'month': 8, 'day': 19, 'title': 'Malou', 'image': 'malou.jpg'},
    {'month': 12, 'day': 25, 'title': 'Navidad', 'image': 'Diciembre.jpg'},
    {'month': 1, 'day': 1, 'title': 'Año Nuevo', 'image': 'Enero.jpg'}
]

def load_titles(year):
    """Load image titles from year-specific titles.txt file or return default titles."""
    titles_path = os.path.join('pics', str(year), 'titles.txt')
    
    if os.path.exists(titles_path):
        try:
            with open(titles_path, 'r', encoding='utf-8') as f:
                # Read non-empty lines and strip whitespace
                titles = [line.strip() for line in f if line.strip()]
                
                # Validate we have exactly 12 titles
                if len(titles) == 12:
                    return titles
                else:
                    print(f"Warning: titles.txt for {year} should contain exactly 12 titles (found {len(titles)})")
                    print("Using default titles instead")
        except Exception as e:
            print(f"Error reading titles.txt for {year}: {e}")
            print("Using default titles instead")
    
    return DEFAULT_TITLES

def create_calendar(year, month, titles):
    # A3 size in pixels at 300 DPI (297mm × 420mm) + 4mm bleed on all sides
    BLEED_MM = 4
    DPI = 300
    MM_TO_INCH = 25.4
    bleed_px = int(BLEED_MM * DPI / MM_TO_INCH)
    
    # New dimensions with bleed
    width = int((297 + 2 * BLEED_MM) * DPI / MM_TO_INCH)  # 3508 + ~94 pixels (approx 3602)
    height = int((420 + 2 * BLEED_MM) * DPI / MM_TO_INCH)  # 4961 + ~94 pixels (approx 5055)
    
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Calculate dimensions in pixels (300 DPI) for the actual content area
    content_width = int(297 * DPI / MM_TO_INCH) # Original A3 width (3508 pixels)
    table_width = content_width
    week_col_width = int(20 * DPI / MM_TO_INCH)  # Approximately 2 cm for week numbers column
    calendar_width = table_width - week_col_width  # Width for the 7 day columns
    cell_width = calendar_width // 7  # Width for each day column
    
    # Calculate positions (relative to the full bleed canvas)
    start_x = bleed_px
    week_col_x = start_x + calendar_width  # Position week numbers column at the end
    first_row_height = int(16.6 * DPI / MM_TO_INCH)  # 1.66 cm converted to pixels at 300 DPI
    cell_height = 340 # Fits larger image area
    
    # Load and process the main image
    image_x = 0 # Start from the very edge of the bleed
    image_y = 0 
    # Photo will cover the top, left, and right bleed. 
    # Its size will be width x (2480 + bleed_px)
    target_photo_height = 2480 + bleed_px
    month_image = load_and_resize_image(month, year, width, target_photo_height)
    image.paste(month_image, (image_x, image_y))
    
    # The border around the main image has been removed as requested.
    
    # Draw the image title at the bottom right of the picture
    image_title = titles[month-1]
    print(f"Image title for month {month}: {image_title}")  # Debug print
    title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)  # Smaller font for the title
    title_width = draw.textlength(image_title, font=title_font)
    title_height = 30  # Approximate height of text
    title_x = width - title_width - bleed_px - 20  # Padding from bleed edge
    title_y = month_image.height - 40  # Under the photo area
    
    # The background behind the text has been removed as requested. Image title drawn directly.
    
    # Draw the text
    draw.text((title_x, title_y), image_title, font=title_font, fill='black')
    
    # Calculate positions for month name and days
    header_y = image_y + month_image.height + 30
    month_area_height = 100  # Height for month name area
    
    # Try to load fonts, fallback to default if not available
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        # 19pt at 300 DPI = (19 * 300/72) ≈ 79 pixels
        day_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 79)
        # 12pt at 300 DPI = (12 * 300/72) ≈ 50 pixels
        week_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
        # 11pt at 300 DPI = (11 * 300/72) ≈ 46 pixels
        header_font = ImageFont.load_default()
        number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 100)
    except:
        title_font = ImageFont.load_default()
        day_font = ImageFont.load_default()
        week_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        number_font = ImageFont.load_default()

    # Draw month and year first (before reflection)
    month_text = f"{MESES[month-1]} {year}"
    text_width = draw.textlength(month_text, font=title_font)
    draw.text(((width - text_width) // 2, header_y + (month_area_height - 60) // 2), month_text, font=title_font, fill='black')
    
    # Create and paste the flipped image in front of month name area
    reflection = month_image.copy()
    reflection = reflection.transpose(Image.FLIP_TOP_BOTTOM)
    
    # Create a temporary image for the visible part of reflection (250px height)
    visible_height = 250
    temp_image = Image.new('RGBA', (table_width, visible_height), (255, 255, 255, 0))
    
    # Crop the top portion of the flipped image
    cropped_reflection = reflection.crop((0, 0, reflection.width, visible_height))
    
    # Make it more visible (50% opacity)
    mask = Image.new('L', cropped_reflection.size, 128)  # Changed from 50 to 128 for more visibility
    cropped_reflection.putalpha(mask)
    
    # Paste the cropped reflection
    temp_image.paste(cropped_reflection, (0, 0), cropped_reflection)
    
    # Paste the visible portion in front of the month name
    image.paste(temp_image, (image_x, header_y - 28), temp_image)
    
    # Update position for days row
    days_y = header_y + month_area_height + 40
    
    # Draw "Semana" header
    week_text = "Semana"
    text_width = draw.textlength(week_text, font=week_font)
    draw.text((week_col_x + (week_col_width - text_width) // 2, days_y + (first_row_height - 50) // 2), 
              week_text, font=week_font, fill='black')
    
    # Draw days
    for i, day in enumerate(DIAS):
        text_width = draw.textlength(day, font=day_font)
        x = start_x + (cell_width * i) + (cell_width - text_width) // 2
        y = days_y + (first_row_height - 79) // 2
        draw.text((x, y), day, font=day_font, fill='black')
    
    # Calculate grid start position
    grid_start_y = days_y + first_row_height
    
    # Get the calendar for the month
    cal = calendar.monthcalendar(year, month)
    
    # Draw the grid and numbers
    start_y = grid_start_y
    
    # Draw horizontal lines
    # First row (header)
    draw.line([(start_x, grid_start_y), (week_col_x + week_col_width, grid_start_y)], fill='black', width=2)
    # Line after header (at first_row_height)
    draw.line([(start_x, start_y), (week_col_x + week_col_width, start_y)], fill='black', width=2)
    # Rest of the rows
    for i in range(1, 7):
        y = start_y + (i * cell_height)
        draw.line([(start_x, y), (week_col_x + week_col_width, y)], fill='black', width=2)

    # Draw vertical lines
    # First draw calendar grid lines
    for i in range(8):
        x = start_x + (i * cell_width)
        draw.line([(x, grid_start_y), (x, start_y + (6 * cell_height))], fill='black', width=2)
    
    # Draw week numbers column line
    draw.line([(week_col_x + week_col_width, grid_start_y), (week_col_x + week_col_width, start_y + (6 * cell_height))], fill='black', width=2)

    # Fill in the numbers and week numbers
    for week_num, week in enumerate(cal):
        # Add week number
        if any(day != 0 for day in week):  # Only add week number if week has days
            # Get the date of the first day of the week that's not 0
            first_day_of_week = next(day for day in week if day != 0)
            week_date = date(year, month, first_day_of_week)
            week_number = week_date.isocalendar()[1]
            week_text = str(week_number)
            text_width = draw.textlength(week_text, font=week_font)
            x = week_col_x + (week_col_width - text_width) // 2
            y = start_y + (week_num * cell_height) + 100
            draw.text((x, y), week_text, font=week_font, fill='black')
        
        # Fill in the days
        for day_num, day in enumerate(week):
            if day != 0:
                # Add background image for special days
                for special_day in SPECIAL_DAYS:
                    if month == special_day['month'] and day == special_day['day']:
                        try:
                            # Try multiple extensions for special images too if not found
                            possible_names = [special_day['image']]
                            base_name = os.path.splitext(special_day['image'])[0]
                            for ext in ['.jpg', '.JPG', '.jpeg', '.JPEG', '.tif', '.TIF', '.tiff', '.TIFF', '.png', '.PNG', '.webp', '.WEBP']:
                                if base_name + ext not in possible_names:
                                    possible_names.append(base_name + ext)
                            
                            special_image_path = None
                            for name in possible_names:
                                path = f"imagenes_ejemplo/{name}"
                                if os.path.exists(path):
                                    special_image_path = path
                                    break
                            
                            if not special_image_path:
                                raise FileNotFoundError(f"Image {special_day['image']} not found")

                            # Load and resize the special image
                            special_image = Image.open(special_image_path)
                            special_image = special_image.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
                            # Make it semi-transparent
                            special_image.putalpha(128)  # 50% opacity
                            # Paste it into the cell
                            cell_x = start_x + day_num * cell_width
                            cell_y = grid_start_y + week_num * cell_height
                            image.paste(special_image, (cell_x, cell_y), special_image)
                            
                            # Add the special day title below the date
                            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)  # Smaller font for the title
                            title_text = special_day['title']
                            title_width = draw.textlength(title_text, font=title_font)
                            title_x = cell_x + (cell_width - title_width) // 2
                            title_y = cell_y + cell_height - 20  # 20px from bottom
                            draw.text((title_x, title_y), title_text, font=title_font, fill='black')
                        except FileNotFoundError:
                            print(f"Warning: Image {special_day['image']} (or variants) not found for {special_day['title']}")
                
                # Draw the day number
                day_text = str(day)
                text_width = draw.textlength(day_text, font=number_font)
                text_x = start_x + day_num * cell_width + (cell_width - text_width) // 2
                text_y = start_y + week_num * cell_height + (cell_height - 50) // 2
                draw.text((text_x, text_y), day_text, font=number_font, fill='black')

    return image

def find_image(month_name, directory):
    """Search for an image with various supported extensions."""
    extensions = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.tif', '.TIF', '.tiff', '.TIFF', '.png', '.PNG', '.webp', '.WEBP']
    for ext in extensions:
        path = os.path.join(directory, f'{month_name}{ext}')
        if os.path.exists(path):
            return path
    return None

def load_and_resize_image(month, year, width=3508, height=2480):
    """Load and resize image for the given month and year. Return a white image if no image exists."""
    month_name = MESES[month-1]
    
    # Try to load the year-specific image first, then fall back to default
    image_path = find_image(month_name, os.path.join('pics', str(year)))
    if not image_path:
        image_path = find_image(month_name, 'imagenes_ejemplo')
    
    try:
        if image_path and os.path.exists(image_path):
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB' and img.mode != 'RGBA':
                    img = img.convert('RGB')
                elif img.mode == 'RGBA':
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3]) # 3 is alpha channel
                    img = background
                
                # Resize maintaining aspect ratio to fill the area OR fit as requested
                # Since the user asked for a specific size, we use thumbnail to fit within it
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                # Create new image with white background
                new_img = Image.new('RGB', (width, height), 'white')
                # Calculate position to center the image
                x = (width - img.width) // 2
                y = (height - img.height) // 2
                # Paste the resized image
                new_img.paste(img, (x, y))
                return new_img
        else:
            if not image_path:
                print(f"Warning: No image found for {month_name} in pics/{year} or imagenes_ejemplo")
            else:
                print(f"Warning: Image not found at {image_path}")
            return Image.new('RGB', (width, height), 'white')
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return Image.new('RGB', (width, height), 'white')

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate calendars for a specific year')
    parser.add_argument('year', type=int, help='Year to generate calendars for')
    args = parser.parse_args()
    
    year = args.year
    
    # Create output directory if it doesn't exist
    output_dir = f"calendarios_{year}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create pics directory for the year if it doesn't exist
    year_pics_dir = os.path.join('pics', str(year))
    if not os.path.exists(year_pics_dir):
        os.makedirs(year_pics_dir)
        print(f"Created directory for year's pictures: {year_pics_dir}")
        print(f"Please add your images for {year} in this directory using names like 'Enero.jpg', 'Febrero.tif', etc.")
        print(f"Supported extensions: .jpg, .jpeg, .tif, .tiff, .png, .webp")
        print("\nOptionally, create a 'titles.txt' file in the same directory with 12 lines,")
        print("each line containing a title for the corresponding month's image.")
    
    # Load titles for the year
    titles = load_titles(year)
    
    # Generate calendars for each month
    for month in range(1, 13):
        output_file = os.path.join(output_dir, f"{MESES[month-1]}.pdf")
        calendar_image = create_calendar(year, month, titles)
        calendar_image.save(output_file)
        print(f"Generated calendar for {MESES[month-1]} {year}")
    
    print(f"Calendarios generados con éxito en la carpeta '{output_dir}'")

if __name__ == "__main__":
    main()
