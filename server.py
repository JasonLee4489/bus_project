from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("demo")

@mcp.tool()
def hello(name: str) -> str:
    return f"Hello {name}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="streamable-http", port=port)
