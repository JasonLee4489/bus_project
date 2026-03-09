from mcp.server.fastmcp import FastMCP
import os

port = int(os.environ.get("PORT", 8000))

mcp = FastMCP("demo", host="0.0.0.0", port=port)

@mcp.tool()
def hello(name: str) -> str:
    return f"Hello {name}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
