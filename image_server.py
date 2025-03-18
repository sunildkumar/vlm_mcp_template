import json
import struct

from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage

mcp = FastMCP("Echo")


def pil_image_to_mcp_image(pil_img: PILImage.Image, format: str = "png") -> Image:
    """
    Convert a PIL Image to an MCP Image with embedded metadata necessary to reconstruct the image.
    
    Args:
        pil_img: The PIL Image object
        format: The format to use for the MCP Image (default: png)
        
    Returns:
        An MCP Image object with embedded metadata. The format of the bytes is:
        [4-byte metadata length][metadata JSON][image bytes]
    """
    width, height = pil_img.size
    mode = pil_img.mode
    image_bytes = pil_img.tobytes()
    
    # Create metadata dictionary
    metadata = {
        "width": width,
        "height": height,
        "mode": mode,
        "format": pil_img.format or format,
    }
    
    # Convert metadata to JSON bytes
    metadata_bytes = json.dumps(metadata).encode('utf-8')
    
    # Structure: [4-byte metadata length][metadata JSON][image bytes]
    # Combine everything into a single byte stream
    combined_data = struct.pack(">I", len(metadata_bytes)) + metadata_bytes + image_bytes
    
    # Return the MCP Image object
    return Image(data=combined_data, format=format)


def mcp_image_to_pil_image(image_data: bytes) -> PILImage.Image:
    """
    Convert MCP Image bytes back to a PIL Image.
    
    Args:
        image_data: The MCP Image bytes with embedded metadata: [4-byte metadata length][metadata JSON][image bytes]
        
    Returns:
        A PIL Image reconstructed from the bytes
    """
    # Extract metadata length (first 4 bytes)
    metadata_length = struct.unpack(">I", image_data[:4])[0]
    
    # Extract and parse metadata
    metadata_bytes = image_data[4:4+metadata_length]
    metadata = json.loads(metadata_bytes.decode('utf-8'))
    
    # Extract image bytes
    image_bytes = image_data[4+metadata_length:]
    
    # Get image properties from metadata
    width = metadata["width"]
    height = metadata["height"]
    mode = metadata["mode"]
    
    # Convert bytes to PIL Image
    img = PILImage.frombytes(mode=mode, size=(width, height), data=image_bytes)
    
    return img


@mcp.tool()
def echo_image(image_path: str) -> Image:
    """
    Echo an image as a tool.
    
    Args:
        image_path: The path to the image file to be echoed.
        
    Returns:
        An MCP Image object containing the echoed image data.
    """
    img = PILImage.open(image_path)
    
    mcp_image = pil_image_to_mcp_image(img)
    
    return mcp_image


@mcp.tool()
def rotate_image(image_path: str, direction: str) -> Image:
    """
    Rotate an image by 90 degrees.

    Args:
        direction: The direction to rotate the image, either 'clockwise' or 'counterclockwise'.
        
    Returns:
        An MCP Image object containing the rotated image data.
    """
    img = PILImage.open(image_path)
    if direction == "clockwise":
        img = img.rotate(-90, expand=True) 
    elif direction == "counterclockwise":
        img = img.rotate(90, expand=True)   
    else:
        raise ValueError("Invalid direction")
    
    mcp_image = pil_image_to_mcp_image(img)
    
    return mcp_image


@mcp.tool()
def crop_and_zoom(image_path: str, x_min: float, y_min: float, x_max: float, y_max: float, zoom_factor: float = 1.0) -> Image:
    """
    Crop and zoom an image based on a normalized bounding box.
    
    Args:
        image_path: The path to the image file to be cropped.
        x_min: Left boundary of crop box (normalized 0-1).
        y_min: Top boundary of crop box (normalized 0-1).
        x_max: Right boundary of crop box (normalized 0-1).
        y_max: Bottom boundary of crop box (normalized 0-1).
        zoom_factor: The factor to zoom by after cropping. Values less than 1.0 will reduce the size, and values greater than 1.0 will increase the size.
    Returns:
        An MCP Image object containing the cropped image data.
    """
    # Validate input coordinates
    if not (0 <= x_min < x_max <= 1 and 0 <= y_min < y_max <= 1):
        raise ValueError("Invalid bounding box coordinates. Must be between 0 and 1 with min < max.")
    
    # Open the image
    img = PILImage.open(image_path)
    width, height = img.size
    
    # Convert normalized coordinates to pixel coordinates
    # Ensure we don't exceed image boundaries by clamping to width-1 and height-1
    left = int(x_min * width)
    top = int(y_min * height)
    right = min(int(x_max * width), width)
    bottom = min(int(y_max * height), height)
    
    # Crop the image
    cropped_img = img.crop((left, top, right, bottom))
    
    # Zoom in
    resized_img = cropped_img.resize((int(cropped_img.width * zoom_factor), int(cropped_img.height * zoom_factor)), PILImage.Resampling.LANCZOS)
    
    # Convert to MCP image and return
    mcp_image = pil_image_to_mcp_image(resized_img)
    
    return mcp_image


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')