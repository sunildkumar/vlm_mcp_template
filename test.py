import base64
import json
import struct

from PIL import Image


def reconstruct_and_display_image(image_data: bytes):
    # Check if image_bytes is a base64 string and decode if needed
    if isinstance(image_data, str):
        image_data = base64.b64decode(image_data)
        
    print(f"There are {len(image_data)} bytes in the image")
    
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
    
    print(f"Image dimensions: {width}x{height}, mode: {mode}")
    
    # convert bytes to image
    img = Image.frombytes(mode=mode, size=(width, height), data=image_bytes)
    
    # Optionally display the image
    img.show()
    
    return img

if __name__ == "__main__":
    with open("bytes.txt", "rb") as file:  # Use 'rb' mode to read binary data
        image_data = file.read()  # Read all binary data
    reconstruct_and_display_image(image_data=image_data)
    