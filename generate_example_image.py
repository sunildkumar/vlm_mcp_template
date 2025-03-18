from PIL import Image, ImageDraw, ImageFont

image_width = 2048
image_height = 2048


def generate_image():
    # Create a new white image (without text)
    base_image = Image.new("RGB", (image_width, image_height), color="white")
    base_draw = ImageDraw.Draw(base_image)
    
    # Draw a large down arrow character on the left side
    draw_arrow_character(base_draw)
    
    # Draw a hollow black box in the top right corner (without text)
    draw_hollow_box(base_draw)
    
    # Save the base image
    base_image.save("base_image.png")
    
    # Create a separate transparent image for text only
    text_overlay = Image.new("RGBA", (image_width, image_height), color=(0, 0, 0, 0))
    
    # Draw the text on the overlay
    draw_upside_down_text(text_overlay)
    
    # Save the text overlay
    text_overlay.save("text_overlay.png")
    
    # Combine the images
    final_image = Image.alpha_composite(base_image.convert("RGBA"), text_overlay)
    
    # Save the combined image
    final_image.save("example_image.png")
    print("Images saved: base_image.png, text_overlay.png, example_image.png")


def draw_arrow_character(draw):
    # Use the down arrow Unicode character: ↓
    arrow_char = "↓"
    
    # Double the font size for the larger image
    font_size = 800  # Doubled from 400
    left_margin = 100  # Doubled from 50
    
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
    # Double the box dimensions
    box_margin = 100  # Doubled from 50
    box_size = 400    # Doubled from 200
    
    # Calculate box coordinates (top right corner)
    top_left = (image_width - box_margin - box_size, box_margin)
    bottom_right = (image_width - box_margin, box_margin + box_size)
    
    # Scale the line width proportionally
    line_width = 6  # Doubled from 3
    draw.rectangle([top_left, bottom_right], outline="black", width=line_width)


def draw_upside_down_text(image):
    # Get the box position (must match the position in draw_hollow_box)
    box_margin = 100  # Doubled from 50
    box_size = 400    # Doubled from 200
    top_left = (image_width - box_margin - box_size, box_margin)
    
    # Create a separate image for just the text at a higher resolution
    text_size = box_size * 6  # Keep the same multiplier for scaling
    text_img = Image.new("RGBA", (text_size, text_size), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # Add text with good resolution - double the font size
    message = "Vision models need multimodal tools"
    font_size = 60  # Doubled from 30
    
    # Try to use a bold font with multiple fallback options
    try:
        # Try various bold fonts that might be available on the system
        font_found = False
        for font_name in ["Arial Bold", "arialbd.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf", 
                          "FreeSansBold.ttf", "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf"]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                print(f"Using font: {font_name}")
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
        print(f"Font loading error: {e}")
        # Final fallback
        font = ImageFont.load_default()
    
    # Keep the same line structure
    lines = [
        "Vision",
        "models",
        "need",
        "multimodal",
        "tools"
    ]
    
    # Scale the line height proportionally
    line_height = font_size + 16  # Doubled spacing from 8 to 16
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
        
        # Draw the text multiple times with slightly larger offsets for the larger font
        for offset in [(0, 0), (2, 0), (0, 2), (2, 2)]:  # Increased offset for larger text
            text_draw.text((x_position + offset[0], y_position + offset[1]), line, fill="black", font=font)
    
    # Save the high-res text for debugging
    text_img.save("text_high_res.png")
    
    # Rotate the text 180 degrees
    rotated_text = text_img.rotate(180, resample=Image.BICUBIC)
    
    # Save the rotated text for debugging
    rotated_text.save("text_rotated.png")
    
    # Resize to the final box size
    final_text = rotated_text.resize((box_size, box_size), Image.LANCZOS)
    
    # Save the resized text for debugging
    final_text.save("text_final.png")
    
    # Paste the text onto the overlay image at the box position
    image.paste(final_text, top_left, final_text)


if __name__ == "__main__":
    generate_image()
