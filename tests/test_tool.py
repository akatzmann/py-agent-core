import pytest
from py_agent_core.tool import tool

def test_tool_decorator_sync():
    @tool
    def add(a: int, b: int = 2) -> int:
        """Add two numbers.
        
        Args:
            a: First number.
            b: Second number.
        """
        return a + b

    assert add.__name__ == "add"
    assert add.definition["type"] == "function"
    assert add.definition["function"]["name"] == "add"
    assert add.definition["function"]["description"] == "Add two numbers."
    
    properties = add.definition["function"]["parameters"]["properties"]
    assert properties["a"]["type"] == "integer"
    assert properties["a"]["description"] == "First number."
    assert properties["b"]["type"] == "integer"
    assert properties["b"]["description"] == "Second number."
    assert properties["b"]["default"] == 2
    
    assert add.definition["function"]["parameters"]["required"] == ["a"]

@pytest.mark.asyncio
async def test_tool_call_sync():
    @tool
    def multiply(x: int, y: int) -> int:
        return x * y

    # Call with JSON string
    res = await multiply('{"x": 3, "y": 4}')
    assert res == 12

@pytest.mark.asyncio
async def test_tool_call_async():
    @tool
    async def fetch_data(key: str) -> str:
        return f"value_{key}"

    res = await fetch_data('{"key": "test"}')
    assert res == "value_test"
