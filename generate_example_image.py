from PIL import Image, ImageDraw, ImageFont

image_width = 1024
image_height = 1024


def generate_image():
    # Create a new white image
    image = Image.new("RGB", (image_width, image_height), color="white")
    draw = ImageDraw.Draw(image)
    
    # Draw a large down arrow character on the left side
    draw_arrow_character(draw)
    
    # Draw a hollow black box in the top right corner
    draw_box_with_text(image, draw)
    
    image.save("example_image.png")
    print("Image saved as example_image.png")


def draw_arrow_character(draw):
    # Use the down arrow Unicode character: ↓
    arrow_char = "↓"
    
    # Define font size and position
    font_size = 400  # Very large font
    left_margin = 50  # Distance from the left edge
    
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


def draw_box_with_text(image, draw):
    # Define box position and size
    box_margin = 50  # Distance from the edges
    box_size = 200   # Size of the box
    
    # Calculate box coordinates (top right corner)
    top_left = (image_width - box_margin - box_size, box_margin)
    bottom_right = (image_width - box_margin, box_margin + box_size)
    
    # Draw the box outline with a specified width
    line_width = 3
    draw.rectangle([top_left, bottom_right], outline="black", width=line_width)
    
    # Add upside-down text inside the box
    message = "Hello"
    font_size = 30
    
    try:
        font = ImageFont.truetype("Arial", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
    
    # Calculate center position of the box
    box_center_x = (top_left[0] + bottom_right[0]) // 2
    box_center_y = (top_left[1] + bottom_right[1]) // 2
    
    # Create a temporary image for the text
    text_img = Image.new('RGBA', (box_size, box_size), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # Get text dimensions
    text_bbox = text_draw.textbbox((0, 0), message, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Draw the text centered in this temporary image
    text_x = (box_size - text_width) // 2
    text_y = (box_size - text_height) // 2
    text_draw.text((text_x, text_y), message, font=font, fill="black")
    
    # Rotate the text 180 degrees (upside down)
    rotated_text = text_img.rotate(180)
    
    # Paste the rotated text onto the main image
    image.paste(rotated_text, top_left, rotated_text)


if __name__ == "__main__":
    generate_image()
