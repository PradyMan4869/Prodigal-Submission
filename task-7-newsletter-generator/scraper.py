import newspaper
from newspaper import Article
from typing import List, Dict
import logging

from config import NEWS_SOURCES

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_articles() -> List[Dict]:
    """
    Scrapes the top articles from the list of news sources.
    
    Returns:
        A list of dictionaries, where each dictionary represents an article.
    """
    all_articles = []
    logging.info("Starting article scraping process...")

    for source_name, url in NEWS_SOURCES.items():
        try:
            logging.info(f"Building paper for: {source_name} ({url})")
            paper = newspaper.build(url, memoize_articles=False, fetch_images=False)
            logging.info(f"Found {len(paper.articles)} articles for {source_name}. Parsing top 5.")
            
            count = 0
            for article_url in paper.articles:
                if count >= 5: # Limit to top 5 articles per source for speed
                    break
                
                article = Article(article_url.url)
                try:
                    article.download()
                    article.parse()

                    if article.title and article.text:
                        all_articles.append({
                            "source": source_name,
                            "title": article.title,
                            "url": article.url,
                            "text": article.text,
                        })
                        count += 1
                        logging.info(f"  - Successfully parsed: {article.title}")
                except Exception as e:
                    logging.warning(f"Could not parse article {article_url.url}: {e}")
        
        except Exception as e:
            logging.error(f"Failed to build or scrape from {source_name}: {e}")

    logging.info(f"Scraping complete. Total articles collected: {len(all_articles)}")
    return all_articles

if __name__ == '__main__':
    # For testing the scraper independently
    articles = scrape_articles()
    print(f"\n--- Scraped {len(articles)} articles ---\n")
    for art in articles:
        print(f"Title: {art['title']}\nSource: {art['source']}\nURL: {art['url']}\n")
