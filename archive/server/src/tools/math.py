from fastmcp import FastMCP

from archive.server.src.services.Calculator import CalculatorService


def register_math_tools(
    mcp: FastMCP,
    calculator: CalculatorService,
):

    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return calculator.add(a, b)

    @mcp.tool
    def subtract(a: int, b: int) -> int:
        """Subtract b from a."""
        return calculator.subtract(a, b)

    @mcp.tool
    def multiply(a: int, b: int) -> int:
        """Multiply two integers."""
        return calculator.multiply(a, b)