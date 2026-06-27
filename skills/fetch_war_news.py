import os
import requests
from datetime import datetime
from typing import Optional
from core.registry import skill


@skill
def fetch_news(topic: str, max_results: int = 5, api_key: Optional[str] = None) -> str:
    """
    Fetch real-time top news headlines for any given topic or query.

    Args:
        topic: The news topic or search query (e.g., "war", "technology", "climate change", "sports").
        max_results: Number of headlines to return (default 5, max 20).
        api_key: NewsAPI.org API key. If not provided, reads from NEWSAPI_KEY environment variable.

    Returns:
        A summary of the top headlines for the requested topic.
    """
    try:
        key = api_key or os.getenv("NEWSAPI_KEY")
        if not key:
            return "Error: NewsAPI key not provided. Please supply an API key or set NEWSAPI_KEY environment variable."

        max_results = min(max(1, max_results), 20)

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_results,
            "apiKey": key,
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return f"Error fetching news: {response.status_code} - {response.text}"

        data = response.json()
        articles = data.get("articles", [])

        if not articles:
            return f"No headlines found for topic: {topic}"

        summary_lines = [f"Top {len(articles)} headlines for '{topic}':\n"]

        for idx, article in enumerate(articles, start=1):
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown source")
            published_at = article.get("publishedAt", "")

            try:
                dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M UTC")
            except Exception:
                formatted_time = published_at

            summary_lines.append(
                f"{idx}. {title}\n   Source: {source} | Published: {formatted_time}\n"
            )

        return "\n".join(summary_lines)

    except requests.exceptions.RequestException as e:
        return f"Network error while fetching news: {str(e)}"
    except Exception as e:
        return f"Unexpected error while retrieving news: {str(e)}"