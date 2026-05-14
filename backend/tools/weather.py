from langchain.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city. Args: city (str) - city name."""
    if city == "北京" or city == "北京市":
        return "sunny"
    return "cloudy"

@tool
def recommend_activity(weather: str) -> str:
    """Recommend activity on certain weather. Args: weather (str) - weather"""
    if weather == "sunny":
        return "go outside"
    elif weather == "cloudy":
        return "stay at home"