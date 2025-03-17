import json
import struct

from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage

mcp = FastMCP("Echo")


def pil_image_to_mcp_image(pil_img: PILImage.Image, format: str = "png") -> Image:
    """
    Convert a PIL Image to an MCP Image with embedded metadata.
    
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


@mcp.tool()
def echo_image(image_path: str) -> Image:
    """Echo an image as a tool"""
    img = PILImage.open(image_path)
    
    mcp_image = pil_image_to_mcp_image(img)
    
    # Write the combined data to file (for debugging/testing)
    with open("bytes.txt", "wb") as file:
        file.write(mcp_image.data)
    
    return mcp_image