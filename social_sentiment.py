import requests
import datetime
from transformers import pipeline
import logging

# === CONFIG ===
FINBERT_MODEL = "ProsusAI/finbert"
SEARCH_TERM = "TSLA"
NUM_TWEETS = 25
NUM_REDDIT = 25

# === SETUP ===
sentiment_pipeline = pipeline("sentiment-analysis", model=FINBERT_MODEL)

# === Twitter using X (requires your own bearer token) ===
TWITTER_BEARER_TOKEN = 'your-twitter-bearer-token-here'

def fetch_twitter_sentiment(query=SEARCH_TERM, count=NUM_TWEETS):
    try:
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        params = {
            'query': query,
            'max_results': min(count, 100),
            'tweet.fields': 'created_at,lang'
        }
        url = 'https://api.twitter.com/2/tweets/search/recent'
        response = requests.get(url, headers=headers, params=params)
        tweets = [t['text'] for t in response.json().get('data', []) if t['lang'] == 'en']
        return score_sentiment(tweets)
    except Exception as e:
        logging.warning(f"Twitter sentiment error: {e}")
        return 0

# === Reddit using Pushshift ===
def fetch_reddit_sentiment(query=SEARCH_TERM, count=NUM_REDDIT):
    try:
        end_time = int(datetime.datetime.utcnow().timestamp())
        url = f"https://api.pushshift.io/reddit/search/comment/?q={query}&size={count}&before={end_time}&subreddit=wallstreetbets"
        response = requests.get(url)
        comments = [c['body'] for c in response.json().get('data', []) if 'body' in c]
        return score_sentiment(comments)
    except Exception as e:
        logging.warning(f"Reddit sentiment error: {e}")
        return 0

# === Sentiment Scoring ===
def score_sentiment(texts):
    try:
        if not texts:
            return 0
        results = sentiment_pipeline(texts)
        score = 0
        for r in results:
            if r['label'] == 'positive':
                score += 1
            elif r['label'] == 'negative':
                score -= 1
        return score / len(results)
    except Exception as e:
        logging.warning(f"Sentiment scoring error: {e}")
        return 0

# === COMBINED ===
def get_combined_sentiment():
    twitter_score = fetch_twitter_sentiment()
    reddit_score = fetch_reddit_sentiment()
    return (twitter_score + reddit_score) / 2

if __name__ == "__main__":
    print("Twitter Sentiment:", fetch_twitter_sentiment())
    print("Reddit Sentiment:", fetch_reddit_sentiment())
    print("Combined Sentiment Score:", get_combined_sentiment())