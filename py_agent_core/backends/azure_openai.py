from typing import AsyncGenerator, List, Dict, Any, Optional
from openai import AsyncAzureOpenAI
from py_agent_core.backends.base import BaseBackend, BackendChunk, ToolCallChunk

class AzureOpenAIBackend(BaseBackend):
    """Adapter for Microsoft Azure OpenAI Service."""
    
    def __init__(self, client: AsyncAzureOpenAI, model: str):
        """
        Args:
            client: An initialized AsyncAzureOpenAI client.
            model: The deployment name or model identifier.
        """
        self.client = client
        self.model = model

    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[BackendChunk, None]:
        kwargs = {}
        if tools:
            kwargs["tools"] = tools

        response_stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs
        )
        
        try:
            async for chunk in response_stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                text_delta = delta.content
                
                tool_calls = None
                if delta.tool_calls:
                    tool_calls = []
                    for tc in delta.tool_calls:
                        tool_calls.append(ToolCallChunk(
                            index=tc.index,
                            id=tc.id,
                            name=tc.function.name if tc.function else None,
                            arguments=tc.function.arguments if (tc.function and tc.function.arguments) else ""
                        ))
                        
                yield BackendChunk(text=text_delta, tool_calls=tool_calls)
        finally:
            # Ensure the connection / stream is closed instantly if execution is aborted
            await response_stream.close()
