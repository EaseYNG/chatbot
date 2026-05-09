from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city. Args: city (str) - city name."""
    if city == "北京" or city == "北京市":
        return "sunny"
    return "cloudy"
