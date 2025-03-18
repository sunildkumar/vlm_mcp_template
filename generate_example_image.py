from PIL import Image, ImageDraw, ImageFont

image_width = 2048
image_height = 2048


def generate_image():
    # Create a new white image
    base_image = Image.new("RGB", (image_width, image_height), color="white")
    base_draw = ImageDraw.Draw(base_image)
    
    # Draw a large down arrow character on the left side
    draw_arrow_character(base_draw)
    
    # Draw a hollow black box in the top right corner
    draw_hollow_box(base_draw)
    
    # Create a separate transparent image for text only
    text_overlay = Image.new("RGBA", (image_width, image_height), color=(0, 0, 0, 0))
    
    # Draw the text on the overlay
    draw_upside_down_text(text_overlay)
    
    # Combine the images
    final_image = Image.alpha_composite(base_image.convert("RGBA"), text_overlay)
    
    # Save the final image
    final_image.save("example_image.png")
    print("Image saved as example_image.png")


def draw_arrow_character(draw):
    # Use the down arrow Unicode character: ↓
    arrow_char = "↓"
    
    # Set font size and position
    font_size = 800
    left_margin = 100
    
    # Try to load a font, or use default if not available
    try:
        font = ImageFont.truetype("Arial", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
    
    # Calculate text size and position
    text_bbox = draw.textbbox((0, 0), arrow_char, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x_position = left_margin
    y_position = (image_height - text_height) // 2
    
    # Draw the arrow character
    draw.text((x_position, y_position), arrow_char, fill="black", font=font)


def draw_hollow_box(draw):
    # Define box dimensions
    box_margin = 100
    box_size = 400
    
    # Calculate box coordinates (top right corner)
    top_left = (image_width - box_margin - box_size, box_margin)
    bottom_right = (image_width - box_margin, box_margin + box_size)
    
    # Draw the box outline
    line_width = 6
    draw.rectangle([top_left, bottom_right], outline="black", width=line_width)


def draw_upside_down_text(image):
    # Get the box position (must match the position in draw_hollow_box)
    box_margin = 100
    box_size = 400
    top_left = (image_width - box_margin - box_size, box_margin)
    
    # Create a separate image for just the text at a higher resolution
    text_size = box_size * 6
    text_img = Image.new("RGBA", (text_size, text_size), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # Add text with good resolution
    font_size = 60
    
    # Try to use a bold font with multiple fallback options
    try:
        # Try various bold fonts that might be available on the system
        font_found = False
        for font_name in ["Arial Bold", "arialbd.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf", 
                          "FreeSansBold.ttf", "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf"]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                font_found = True
                break
            except IOError:
                continue
        
        # If no bold font was found, use regular font but make it thicker
        if not font_found:
            print("No bold font found, using regular font with simulated boldness")
            try:
                font = ImageFont.truetype("Arial", font_size)
            except IOError:
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()
    except Exception as e:
        raise Exception(f"No font found: {e}")
    
    # Text lines
    lines = [
        "Vision",
        "models",
        "need",
        "multimodal",
        "tools"
    ]
    
    # Set line spacing
    line_height = font_size + 16
    total_height = len(lines) * line_height
    
    # Calculate starting position to center text
    start_y = (text_size - total_height) // 2
    
    # Draw each line
    for i, line in enumerate(lines):
        # Get text dimensions
        text_bbox = text_draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        
        # Center the text horizontally
        x_position = (text_size - text_width) // 2
        y_position = start_y + (i * line_height)
        
        # Draw the text multiple times with slight offsets for a bold effect
        for offset in [(0, 0), (2, 0), (0, 2), (2, 2)]:
            text_draw.text((x_position + offset[0], y_position + offset[1]), line, fill="black", font=font)
    
    # Rotate the text 180 degrees
    rotated_text = text_img.rotate(180, resample=Image.BICUBIC)
    
    # Resize to the final box size
    final_text = rotated_text.resize((box_size, box_size), Image.LANCZOS)
    
    # Paste the text onto the overlay image at the box position
    image.paste(final_text, top_left, final_text)


if __name__ == "__main__":
    generate_image()
