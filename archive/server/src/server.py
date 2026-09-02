from fastmcp import FastMCP

from archive.server.src.services.Calculator import CalculatorService
from archive.server.src.tools.math import register_math_tools


def create_server() -> FastMCP:

    mcp = FastMCP(
        name="Requirements MCP Server"
    )

    calculator = CalculatorService()

    register_math_tools(
        mcp=mcp,
        calculator=calculator,
    )

    return mcp


mcp = create_server()


if __name__ == "__main__":
    mcp.run()