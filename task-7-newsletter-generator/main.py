import time
import schedule
import logging
import asyncio
import os
from datetime import datetime
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import (
    OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    NUM_ARTICLES_TO_SELECT, SIMILARITY_THRESHOLD,
    SCHEDULE_MODE, TESTING_INTERVAL_MINUTES, DAILY_RUN_TIME
)
import scraper
import agents
import telegram_sender

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """
    Deduplicates a list of articles based on title similarity.
    """
    if not articles:
        return []

    vectorizer = TfidfVectorizer().fit_transform([a['title'] for a in articles])
    cosine_sim_matrix = cosine_similarity(vectorizer)
    
    unique_indices = set(range(len(articles)))
    indices_to_remove = set()

    for i in range(len(articles)):
        if i in indices_to_remove:
            continue
        for j in range(i + 1, len(articles)):
            if j in indices_to_remove:
                continue
            if cosine_sim_matrix[i, j] > SIMILARITY_THRESHOLD:
                # Mark the duplicate for removal
                indices_to_remove.add(j)
    
    unique_articles = [articles[i] for i in sorted(list(unique_indices - indices_to_remove))]
    logging.info(f"Deduplication complete. Reduced from {len(articles)} to {len(unique_articles)} articles.")
    return unique_articles


async def run_newsletter_job():
    """
    The main job function that orchestrates the entire newsletter generation process.
    """
    logging.info("--- Starting new newsletter generation job ---")

    # 1. Scrape articles
    articles = scraper.scrape_articles()
    if not articles:
        logging.warning("No articles were scraped. Aborting job.")
        return

    # 2. Deduplicate similar news
    unique_articles = deduplicate_articles(articles)
    
    # 3. Identify top N articles
    top_articles = unique_articles[:NUM_ARTICLES_TO_SELECT]
    logging.info(f"Selected top {len(top_articles)} articles for summarization.")

    # 4. Generate summary via LangChain agents
    summarizer_chain = agents.get_summarizer_chain()
    summaries = [
        f"*{article['title']}*\n{agents.summarize_article(article, summarizer_chain)}\n(Source: [{article['source']}]({article['url']}))"
        for article in top_articles
    ]
    formatted_summaries = "\n\n".join(summaries)
    
    # 5. Compose newsletter
    logging.info("Composing the final newsletter...")
    composer_chain = agents.get_newsletter_composer_chain()
    newsletter_result = composer_chain.invoke({"summaries": formatted_summaries})
    final_newsletter = newsletter_result['text']
    
    # Save a sample for deliverables
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_path = f"output/newsletter_{timestamp}.md"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_newsletter)
    logging.info(f"Newsletter sample saved to {output_path}")

    # 6. Push daily to Telegram group via bot
    await telegram_sender.send_telegram_message(final_newsletter)
    
    logging.info("--- Newsletter generation job finished ---")


def main():
    """
    Sets up the scheduler and runs the main loop.
    """
    # Check for required environment variables
    if not OPENAI_API_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Missing critical environment variables (OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).")
        logging.error("Please set them and restart the application.")
        return

    logging.info("Newsletter Generator started.")
    logging.info(f"Scheduler mode: {SCHEDULE_MODE}")

    # Set up the schedule
    if SCHEDULE_MODE == 'testing':
        schedule.every(TESTING_INTERVAL_MINUTES).minutes.do(lambda: asyncio.run(run_newsletter_job()))
        logging.info(f"Job scheduled to run every {TESTING_INTERVAL_MINUTES} minutes for testing.")
    else: # 'daily' mode
        schedule.every().day.at(DAILY_RUN_TIME).do(lambda: asyncio.run(run_newsletter_job()))
        logging.info(f"Job scheduled to run daily at {DAILY_RUN_TIME} UTC.")

    # Run the job once immediately on startup for demonstration
    logging.info("Running an initial job on startup...")
    asyncio.run(run_newsletter_job())

    # Main loop to run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
