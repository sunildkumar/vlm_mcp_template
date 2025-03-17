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
            
            expected_tools = ["echo_image", "rotate_image"]
            

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
    
            
            
            
            
            
            
            
            
            
    
