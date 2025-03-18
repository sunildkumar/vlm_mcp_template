import base64
import re
from contextlib import asynccontextmanager

import numpy as np
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image as PILImage

from image_server import mcp_image_to_pil_image


class TestImageServer:
    def setup_method(self):
        # Server parameters for stdio connection
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "image_server.py"],
            env=None,
        )
        
        self.image_path = "demo.png"
        
        self.original_image = PILImage.open(self.image_path)
    
    @asynccontextmanager
    async def get_session(self): 
        '''
        Context manager of context managers that starts a session with the MCP server so we can try querying it
        '''
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        '''
        Verifies that the expected tools exist
        '''
        async with self.get_session() as session:
            tools = await session.list_tools()
            
            tools = str(tools)
            
            expected_tools = ["echo_image", "rotate_image", "crop_and_zoom"]
            

            actual_tools = re.findall(r"name='([^']*)'", tools)
            
            assert tools is not None
            assert sorted(actual_tools) == sorted(expected_tools)
    
    @pytest.mark.asyncio
    async def test_echo_image(self):
        '''
        Verifies that the echo_image tool works. It should return bytes that can be reconstructed into the original PIL image
        '''
        
        async with self.get_session() as session:
            result = await session.call_tool("echo_image", arguments={"image_path": self.image_path})
            assert len(result.content) == 1
            image_bytes_str = result.content[0].data
            
            image_bytes = base64.b64decode(image_bytes_str)

            mcp_image = mcp_image_to_pil_image(image_bytes)
            
            # Convert images to numpy arrays for pixel comparison
            original_array = np.array(self.original_image)
            echo_array = np.array(mcp_image)
            
            # Verify images have same dimensions
            assert original_array.shape == echo_array.shape, "Images have different dimensions"
            
            # Verify all pixels are identical
            assert np.array_equal(original_array, echo_array), "Images are not identical pixelwise"
    
    @pytest.mark.asyncio
    async def test_rotate_image(self):
        '''
        Verifies that the rotate_image tool works correctly by comparing server-rotated
        images with locally rotated images using PIL
        '''
        async with self.get_session() as session:
            # Test clockwise rotation
            clockwise_result = await session.call_tool(
                "rotate_image", 
                arguments={"image_path": self.image_path, "direction": "clockwise"}
            )
            assert len(clockwise_result.content) == 1
            clockwise_bytes = base64.b64decode(clockwise_result.content[0].data)
            server_clockwise_image = mcp_image_to_pil_image(clockwise_bytes)
            
            # Create the same rotation locally with PIL
            local_clockwise_image = self.original_image.rotate(-90, expand=True)
            
            # Test counterclockwise rotation
            counterclockwise_result = await session.call_tool(
                "rotate_image", 
                arguments={"image_path": self.image_path, "direction": "counterclockwise"}
            )
            assert len(counterclockwise_result.content) == 1
            counterclockwise_bytes = base64.b64decode(counterclockwise_result.content[0].data)
            server_counterclockwise_image = mcp_image_to_pil_image(counterclockwise_bytes)
            
            # Create the same rotation locally with PIL
            local_counterclockwise_image = self.original_image.rotate(90, expand=True)
            
            # Convert images to numpy arrays for comparison
            server_clockwise_array = np.array(server_clockwise_image)
            local_clockwise_array = np.array(local_clockwise_image)
            server_counterclockwise_array = np.array(server_counterclockwise_image)
            local_counterclockwise_array = np.array(local_counterclockwise_image)
            
            # Verify dimensions match
            assert server_clockwise_array.shape == local_clockwise_array.shape
            assert server_counterclockwise_array.shape == local_counterclockwise_array.shape
            
            # Verify the server-rotated images match the locally-rotated images
            assert np.array_equal(server_clockwise_array, local_clockwise_array), "Clockwise rotation doesn't match"
            assert np.array_equal(server_counterclockwise_array, local_counterclockwise_array), "Counterclockwise rotation doesn't match"
    
    @pytest.mark.asyncio
    async def test_basic_crop(self):
        '''
        Verifies that the crop_and_zoom tool works correctly for a basic crop operation
        with default zoom factor (1.0) by comparing server-cropped image with locally
        cropped image using PIL
        '''
        # Define crop coordinates (normalized 0-1)
        x_min, y_min, x_max, y_max = 0.25, 0.25, 0.75, 0.75
        
        async with self.get_session() as session:
            # Call the crop_and_zoom tool with default zoom factor (1.0)
            crop_result = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max
                }
            )
            
            # Process the result
            assert len(crop_result.content) == 1
            crop_bytes = base64.b64decode(crop_result.content[0].data)
            server_cropped_image = mcp_image_to_pil_image(crop_bytes)
            
            # Create the same crop locally with PIL
            width, height = self.original_image.size
            left = int(x_min * width)
            top = int(y_min * height)
            right = int(x_max * width)
            bottom = int(y_max * height)
            local_cropped_image = self.original_image.crop((left, top, right, bottom))
            
            # Convert images to numpy arrays for comparison
            server_crop_array = np.array(server_cropped_image)
            local_crop_array = np.array(local_cropped_image)
            
            # Verify dimensions match
            assert server_crop_array.shape == local_crop_array.shape, "Cropped image dimensions don't match"
            
            # Verify the server-cropped image matches the locally-cropped image
            assert np.array_equal(server_crop_array, local_crop_array), "Cropped image content doesn't match"
    
    @pytest.mark.asyncio
    async def test_zoom_in(self):
        '''
        Verifies that the crop_and_zoom tool works correctly with a zoom factor greater 
        than 1.0 (zooming in) by comparing server-processed image with locally 
        processed image using PIL
        '''
        # Define crop coordinates (normalized 0-1)
        x_min, y_min, x_max, y_max = 0.3, 0.3, 0.7, 0.7
        zoom_factor = 2.0  # Enlarge the image by 2x
        
        async with self.get_session() as session:
            # Call the crop_and_zoom tool with zoom factor > 1.0
            zoom_result = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max,
                    "zoom_factor": zoom_factor
                }
            )
            
            # Process the result
            assert len(zoom_result.content) == 1
            zoom_bytes = base64.b64decode(zoom_result.content[0].data)
            server_zoomed_image = mcp_image_to_pil_image(zoom_bytes)
            
            # Create the same crop and zoom locally with PIL
            width, height = self.original_image.size
            left = int(x_min * width)
            top = int(y_min * height)
            right = int(x_max * width)
            bottom = int(y_max * height)
            
            # First crop the image
            local_cropped_image = self.original_image.crop((left, top, right, bottom))
            
            # Then resize it according to zoom factor using the same resampling method
            local_zoomed_image = local_cropped_image.resize(
                (int(local_cropped_image.width * zoom_factor), 
                 int(local_cropped_image.height * zoom_factor)),
                PILImage.Resampling.LANCZOS
            )
            
            # Convert images to numpy arrays for comparison
            server_zoom_array = np.array(server_zoomed_image)
            local_zoom_array = np.array(local_zoomed_image)
            
            # Verify dimensions match
            assert server_zoom_array.shape == local_zoom_array.shape, "Zoomed image dimensions don't match"
            
            # Verify the image content matches
            assert np.array_equal(server_zoom_array, local_zoom_array), "Zoomed image content doesn't match"
    
    @pytest.mark.asyncio
    async def test_zoom_out(self):
        '''
        Verifies that the crop_and_zoom tool works correctly with a zoom factor less
        than 1.0 (zooming out) by comparing server-processed image with locally 
        processed image using PIL
        '''
        # Define crop coordinates (normalized 0-1)
        x_min, y_min, x_max, y_max = 0.1, 0.1, 0.9, 0.9
        zoom_factor = 0.5  # Reduce the image size by half
        
        async with self.get_session() as session:
            # Call the crop_and_zoom tool with zoom factor < 1.0
            zoom_result = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max,
                    "zoom_factor": zoom_factor
                }
            )
            
            # Process the result
            assert len(zoom_result.content) == 1
            zoom_bytes = base64.b64decode(zoom_result.content[0].data)
            server_zoomed_image = mcp_image_to_pil_image(zoom_bytes)
            
            # Create the same crop and zoom locally with PIL
            width, height = self.original_image.size
            left = int(x_min * width)
            top = int(y_min * height)
            right = int(x_max * width)
            bottom = int(y_max * height)
            
            # First crop the image
            local_cropped_image = self.original_image.crop((left, top, right, bottom))
            
            # Then resize it according to zoom factor using the same resampling method
            local_zoomed_image = local_cropped_image.resize(
                (int(local_cropped_image.width * zoom_factor), 
                 int(local_cropped_image.height * zoom_factor)),
                PILImage.Resampling.LANCZOS
            )
            
            # Convert images to numpy arrays for comparison
            server_zoom_array = np.array(server_zoomed_image)
            local_zoom_array = np.array(local_zoomed_image)
            
            # Verify dimensions match
            assert server_zoom_array.shape == local_zoom_array.shape, "Zoomed out image dimensions don't match"
            
            # Verify the image content matches
            assert np.array_equal(server_zoom_array, local_zoom_array), "Zoomed out image content doesn't match"
    
    @pytest.mark.asyncio
    async def test_full_image_crop(self):
        '''
        Verifies that the crop_and_zoom tool works correctly when cropping the entire image
        (using coordinates 0,0,1,1) by comparing the result with the original image
        '''
        # Define coordinates to crop the entire image (normalized 0-1)
        x_min, y_min, x_max, y_max = 0.0, 0.0, 1.0, 1.0
        
        async with self.get_session() as session:
            # Call the crop_and_zoom tool with coordinates for full image
            crop_result = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max
                }
            )
            
            # Process the result
            assert len(crop_result.content) == 1
            crop_bytes = base64.b64decode(crop_result.content[0].data)
            server_cropped_image = mcp_image_to_pil_image(crop_bytes)
            
            # Create the same crop locally with PIL
            width, height = self.original_image.size
            left = int(x_min * width)
            top = int(y_min * height)
            right = int(x_max * width)
            bottom = int(y_max * height)
            local_cropped_image = self.original_image.crop((left, top, right, bottom))
            
            # Convert images to numpy arrays for comparison
            server_crop_array = np.array(server_cropped_image)
            local_crop_array = np.array(local_cropped_image)
            original_array = np.array(self.original_image)
            
            # Verify dimensions match the original image
            assert server_crop_array.shape == original_array.shape, "Full image crop dimensions don't match original"
            assert local_crop_array.shape == original_array.shape, "Local full image crop dimensions don't match original"
            
            # Verify the server-cropped image matches the original image
            assert np.array_equal(server_crop_array, original_array), "Full image crop doesn't match original image"
            
            # Verify the server-cropped image matches the locally-cropped image
            assert np.array_equal(server_crop_array, local_crop_array), "Full image crop doesn't match local crop"
    
    @pytest.mark.asyncio
    async def test_small_region_crop(self):
        '''
        Verifies that the crop_and_zoom tool works correctly when cropping a very small
        region of the image by comparing server-processed image with locally processed
        image using PIL
        '''
        # Define coordinates to crop a very small region (normalized 0-1)
        x_min, y_min, x_max, y_max = 0.45, 0.45, 0.55, 0.55  # Just 10% of the image in the center
        
        async with self.get_session() as session:
            # Call the crop_and_zoom tool with coordinates for a small region
            crop_result = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": x_min,
                    "y_min": y_min,
                    "x_max": x_max,
                    "y_max": y_max
                }
            )
            
            # Process the result
            assert len(crop_result.content) == 1
            crop_bytes = base64.b64decode(crop_result.content[0].data)
            server_cropped_image = mcp_image_to_pil_image(crop_bytes)
            
            # Create the same crop locally with PIL
            width, height = self.original_image.size
            left = int(x_min * width)
            top = int(y_min * height)
            right = min(int(x_max * width), width)
            bottom = min(int(y_max * height), height)
            local_cropped_image = self.original_image.crop((left, top, right, bottom))
            
            # Convert images to numpy arrays for comparison
            server_crop_array = np.array(server_cropped_image)
            local_crop_array = np.array(local_cropped_image)
            
            # Verify dimensions match
            assert server_crop_array.shape == local_crop_array.shape, "Small region crop dimensions don't match"
            
            # Verify the server-cropped image matches the locally-cropped image
            assert np.array_equal(server_crop_array, local_crop_array), "Small region crop content doesn't match"
            
            # Additional check: verify the dimensions of the result are exactly as expected
            # Calculate expected dimensions using same algorithm as the server
            expected_width = right - left
            expected_height = bottom - top
            
            # The cropped dimensions should match our calculations exactly
            assert server_cropped_image.width == expected_width, f"Small region crop width incorrect: got {server_cropped_image.width}, expected {expected_width}"
            assert server_cropped_image.height == expected_height, f"Small region crop height incorrect: got {server_cropped_image.height}, expected {expected_height}"
    
    @pytest.mark.asyncio
    async def test_invalid_coordinates(self):
        '''
        Verifies that the crop_and_zoom tool correctly handles invalid coordinates
        by returning appropriate error responses
        '''
        async with self.get_session() as session:
            # Test case 1: x_min > x_max
            response = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": 0.8,
                    "y_min": 0.2,
                    "x_max": 0.3,  # Less than x_min
                    "y_max": 0.7
                }
            )
            assert len(response.content) == 1
            response_content = response.content[0]
            # Verify response has error information
            assert "Invalid bounding box coordinates" in response_content.text
            
            # Test case 2: y_min > y_max
            response = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": 0.2,
                    "y_min": 0.8,
                    "x_max": 0.7,
                    "y_max": 0.3  # Less than y_min
                }
            )
            assert len(response.content) == 1
            response_content = response.content[0]
            # Verify response has error information
            assert "Invalid bounding box coordinates" in response_content.text
            
            # Test case 3: Coordinates outside the 0-1 range (negative)
            response = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": -0.2,  # Negative value
                    "y_min": 0.2,
                    "x_max": 0.7,
                    "y_max": 0.8
                }
            )
            assert len(response.content) == 1
            response_content = response.content[0]
            # Verify response has error information
            assert "Invalid bounding box coordinates" in response_content.text
            
            # Test case 4: Coordinates outside the 0-1 range (greater than 1)
            response = await session.call_tool(
                "crop_and_zoom",
                arguments={
                    "image_path": self.image_path,
                    "x_min": 0.2,
                    "y_min": 0.2,
                    "x_max": 1.2,  # Greater than 1
                    "y_max": 0.8
                }
            )
            assert len(response.content) == 1
            response_content = response.content[0]
            # Verify response has error information
            assert "Invalid bounding box coordinates" in response_content.text
    
    
    

            
