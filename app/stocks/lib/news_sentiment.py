import os
import requests

from .data import fetch_stock_stories_without_sentiment, update_stock_story_sentiment
from .constants import SENTIMENT_PROMPT, NewsSentiment


class SentimentException(Exception):
    pass


def query_hf(payload, model_id) -> list:
    headers = {"Authorization": f"Bearer {os.environ["HUGGINGFACEHUB_API_TOKEN"]}"}
    API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception("Error response from huggingface inference api")
    return response.json()


def categorize_news_sentiment(news: str) -> NewsSentiment:
    repo_id = "mistralai/Mistral-7B-Instruct-v0.3"
    prompt = SENTIMENT_PROMPT.format(news)
    
    res = query_hf(
        {"inputs": prompt, "parameters": {"return_full_text": False}},
        repo_id,
    )
    if not len(res) or "generated_text" not in res[0]:
        raise Exception("Invalid response from huggingface inference")
    
    sentiment: str = res[0]["generated_text"].lower().strip()
    if sentiment not in NewsSentiment:
        raise SentimentException("Invalid sentiment response from huggingface inference", sentiment)

    return NewsSentiment(sentiment)


def set_news_sentiment(stock_isin: str) -> None:
    """
    Sets the sentiment of the news stories for a given stock.
    """
    stories = fetch_stock_stories_without_sentiment(stock_isin)
    for story in stories:
        try:
            print("Categorizing sentiment for story", story["title"])
            sentiment = categorize_news_sentiment(story["text_content"])
            print("Sentiment:", sentiment)
        except SentimentException as e:
            print(e)
            continue

        update_stock_story_sentiment(stock_isin, story["source_url"], sentiment)
