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
    async def test_crop_and_zoom(self):
        '''
        Verifies that the crop_and_zoom tool works correctly by comparing server-processed
        images with locally processed images using PIL
        '''
        async with self.get_session() as session:
            # Test cropping the middle part of the image (25% to 75% on both axes)
            x_min, y_min = 0.25, 0.25
            x_max, y_max = 0.75, 0.75
            
            # Call the server's crop_and_zoom tool
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
            
            assert len(crop_result.content) == 1
            crop_bytes = base64.b64decode(crop_result.content[0].data)
            server_cropped_image = mcp_image_to_pil_image(crop_bytes)
            
            # Create the same crop locally with PIL
            width, height = self.original_image.size
            left = int(x_min * width)
            top = int(y_min * height)
            right = int(x_max * width)
            bottom = int(y_max * height)
            
            # Crop the image
            cropped_img = self.original_image.crop((left, top, right, bottom))
            
            # Calculate the scaling factor to fit the cropped image back to original dimensions
            # while preserving aspect ratio
            crop_width, crop_height = cropped_img.size
            width_ratio = width / crop_width
            height_ratio = height / crop_height
            scale_factor = min(width_ratio, height_ratio)
            
            # Calculate new dimensions
            new_width = int(crop_width * scale_factor)
            new_height = int(crop_height * scale_factor)
            
            # Resize the cropped image
            local_cropped_image = cropped_img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
            
            # Convert images to numpy arrays for comparison
            server_crop_array = np.array(server_cropped_image)
            local_crop_array = np.array(local_cropped_image)
            
            # Verify dimensions match
            assert server_crop_array.shape == local_crop_array.shape, "Cropped image dimensions don't match"
            
            # Verify the server-cropped image matches the locally-cropped image
            assert np.array_equal(server_crop_array, local_crop_array), "Cropped images don't match"
            
            # Test cropping the top-left corner of the image (0% to 40% on both axes)
            x_min, y_min = 0.0, 0.0
            x_max, y_max = 0.4, 0.4
            
            # Call the server's crop_and_zoom tool
            corner_crop_result = await session.call_tool(
                "crop_and_zoom", 
                arguments={
                    "image_path": self.image_path, 
                    "x_min": x_min, 
                    "y_min": y_min, 
                    "x_max": x_max, 
                    "y_max": y_max
                }
            )
            
            assert len(corner_crop_result.content) == 1
            corner_crop_bytes = base64.b64decode(corner_crop_result.content[0].data)
            server_corner_image = mcp_image_to_pil_image(corner_crop_bytes)
            
            # Create the same crop locally with PIL
            left = int(x_min * width)
            top = int(y_min * height)
            right = int(x_max * width)
            bottom = int(y_max * height)
            
            # Crop the image
            corner_cropped_img = self.original_image.crop((left, top, right, bottom))
            
            # Calculate the scaling factor to fit the cropped image back to original dimensions
            corner_width, corner_height = corner_cropped_img.size
            width_ratio = width / corner_width
            height_ratio = height / corner_height
            scale_factor = min(width_ratio, height_ratio)
            
            # Calculate new dimensions
            new_width = int(corner_width * scale_factor)
            new_height = int(corner_height * scale_factor)
            
            # Resize the cropped image
            local_corner_image = corner_cropped_img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
            
            # Convert images to numpy arrays for comparison
            server_corner_array = np.array(server_corner_image)
            local_corner_array = np.array(local_corner_image)
            
            # Verify dimensions match
            assert server_corner_array.shape == local_corner_array.shape, "Corner crop dimensions don't match"
            
            # Verify the server-cropped image matches the locally-cropped image
            assert np.array_equal(server_corner_array, local_corner_array), "Corner crop images don't match"
    
    @pytest.mark.asyncio
    async def test_crop_and_zoom_invalid_coordinates(self):
        '''
        Verifies that the crop_and_zoom tool properly handles invalid coordinates
        '''
        async with self.get_session() as session:
            
            # Test with x_min > x_max
            result = await session.call_tool(
                "crop_and_zoom", 
                arguments={
                    "image_path": self.image_path, 
                    "x_min": 0.8, 
                    "y_min": 0.2, 
                    "x_max": 0.5, 
                    "y_max": 0.7
                }
            )
            
            result = str(result)
            assert "Invalid bounding box" in result

            
            # Test with coordinates outside the valid range (0-1)
            result = await session.call_tool(
                "crop_and_zoom", 
                arguments={
                    "image_path": self.image_path, 
                    "x_min": -0.2, 
                    "y_min": 0.2, 
                    "x_max": 0.5, 
                    "y_max": 0.7
                }
            )
            
            result = str(result)
            assert "Invalid bounding box" in result
            
            # Test with coordinates outside the valid range (0-1)
            result = await session.call_tool(
                "crop_and_zoom", 
                arguments={
                    "image_path": self.image_path, 
                    "x_min": 0.2, 
                    "y_min": 0.2, 
                    "x_max": 1.5, 
                    "y_max": 0.7
                }
            )
            
            result = str(result)
            assert "Invalid bounding box" in result
            
