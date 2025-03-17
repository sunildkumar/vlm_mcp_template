import re
from contextlib import asynccontextmanager

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TestImageServer:
    def setup_method(self):
        # Server parameters for stdio connection
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "python", "image_server.py"],
            env=None,
        )
    
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
    
