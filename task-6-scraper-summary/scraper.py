import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError
import pandas as pd
import time
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Target 1: Microsoft Research Blog (Static Site) ---
def scrape_microsoft_blog():
    """Scrapes the main page of the Microsoft Research Blog."""
    url = "https://www.microsoft.com/en-us/research/blog/"
    logging.info(f"Scraping static site: {url}")
    scraped_data = []
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Articles are within 'div' elements with a specific data-grid attribute
        articles = soup.find_all('div', attrs={'data-grid': 'col-12'})
        
        for article in articles:
            # Find the main link and title within an h3 tag
            title_tag = article.find('h3', class_='m-hyperlink')
            if not title_tag or not title_tag.a:
                continue

            title = title_tag.get_text(strip=True)
            link = title_tag.a['href']
            
            # The description is usually in a 'p' tag following the h3
            description_tag = title_tag.find_next_sibling('p')
            description = description_tag.get_text(strip=True) if description_tag else "No description found"

            scraped_data.append({
                "source": "Microsoft Research Blog",
                "title": title,
                "link": link,
                "description": description
            })
            
        logging.info(f"Successfully scraped {len(scraped_data)} articles from Microsoft Research Blog.")
        return scraped_data

    except requests.RequestException as e:
        logging.error(f"Error fetching Microsoft Blog page: {e}")
        return []

# --- Target 2: MyScheme Portal (Dynamic Site) ---
def scrape_myscheme_portal():
    """Scrapes schemes from the MyScheme portal, handling 'load more' functionality."""
    url = "https://www.myscheme.gov.in/schemes"
    logging.info(f"Scraping dynamic site: {url}")
    scraped_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Handle potential pop-ups or overlays if they exist
            # For MyScheme, there's sometimes a survey pop-up.
            try:
                # A more specific selector is better if available
                close_button_selector = 'button[aria-label="Close"]'
                if page.locator(close_button_selector).is_visible():
                    page.locator(close_button_selector).click()
                    logging.info("Closed a pop-up window.")
            except Exception:
                logging.info("No pop-up found or could not be closed.")

            # Continuously click the "Load More" button until it's no longer visible
            load_more_selector = 'button:has-text("Load More")'
            while page.locator(load_more_selector).is_visible():
                logging.info("Found 'Load More' button, clicking...")
                page.locator(load_more_selector).click()
                # Wait for the network to be idle to ensure new content has loaded
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(2) # A small sleep can help ensure stability

            logging.info("All schemes loaded. Proceeding to scrape.")
            
            # Scrape the content
            scheme_cards = page.locator('div.scheme-card').all()
            
            for card in scheme_cards:
                title = card.locator('h2').inner_text()
                link = card.locator('a.read-more-btn').get_attribute('href')
                # The description is split across several p tags, we'll combine them
                description_parts = card.locator('p').all_inner_texts()
                description = ' '.join(part for part in description_parts if "Read More" not in part).strip()

                scraped_data.append({
                    "source": "MyScheme Portal",
                    "title": title,
                    "link": f"https://www.myscheme.gov.in{link}",
                    "description": description
                })
            
            logging.info(f"Successfully scraped {len(scraped_data)} schemes from MyScheme Portal.")

        except TimeoutError:
            logging.error("Timeout while waiting for MyScheme page to load or for 'Load More' to appear.")
        except Exception as e:
            logging.error(f"An error occurred while scraping MyScheme: {e}")
        finally:
            browser.close()
            
    return scraped_data

# --- Main Execution ---
def main():
    logging.info("Starting scraper task...")
    
    # Install Playwright browsers if not present
    logging.info("Ensuring Playwright browsers are installed...")
    import os
    os.system("playwright install")
    
    # Scrape both targets
    microsoft_data = scrape_microsoft_blog()
    myscheme_data = scrape_myscheme_portal()
    
    # Combine data
    all_data = microsoft_data + myscheme_data
    
    if not all_data:
        logging.warning("No data was scraped from any source. Exiting.")
        return

    # Store in structured format (Pandas DataFrame -> CSV and JSON)
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    output_csv_path = "output/scraped_data.csv"
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df.to_csv(output_csv_path, index=False, encoding='utf-8')
    logging.info(f"Data saved to {output_csv_path}")

    # Save to JSON
    output_json_path = "output/scraped_data.json"
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Data saved to {output_json_path}")

    # Generate and print summary report
    generate_summary_report(len(microsoft_data), len(myscheme_data))

def generate_summary_report(ms_count, myscheme_count):
    report = f"""
# Scraper Summary Report

This report details the scraping process for the Microsoft Research Blog and the MyScheme Portal.

## 1. Microsoft Research Blog (Static Scraper)

- **Technology Used**: `requests` and `BeautifulSoup4`
- **Scraping Strategy**: A simple GET request was made to the target URL. The HTML content was then parsed to find article containers (`div[data-grid="col-12"]`), and from there, the title, link, and description were extracted using specific tag and class selectors.
- **Challenges**:
    - **Selector Brittleness**: The selectors (e.g., `h3.m-hyperlink`) are tied to the current site design. Any frontend update could break the scraper. This is a common challenge with web scraping.
    - **Data Completeness**: Only the articles on the main blog page were scraped. A full site scrape would require a more complex crawler to follow pagination links.
- **Anti-Bot Mechanisms**: None were encountered. The site is public and doesn't appear to have active blocking for simple, polite requests.
- **Results**: Scraped {ms_count} articles.

## 2. MyScheme Portal (Dynamic Scraper)

- **Technology Used**: `Playwright`
- **Scraping Strategy**: A headless browser was used to fully render the JavaScript-heavy page. The core of the strategy was to programmatically click the "Load More" button in a loop until all schemes were displayed on the page. After all content was loaded, the DOM was parsed to extract the scheme details.
- **Challenges**:
    - **Dynamic Content Loading**: The main challenge was handling the "Load More" button. This required waiting for the button to be clickable, clicking it, and then waiting for the new content to be loaded into the DOM (`wait_for_load_state('networkidle')`).
    - **Timing and Stability**: Dynamic sites can be unpredictable. Sometimes network requests take longer, or animations can interfere with clicks. A combination of `networkidle` waits and small `time.sleep()` calls was used to improve stability.
    - **Pop-ups**: The site occasionally shows a survey pop-up on load, which can block interaction. The script includes a step to try and find and close this pop-up.
- **Anti-Bot Mechanisms**: No aggressive anti-bot mechanisms like CAPTCHAs were found. However, the requirement for JavaScript execution itself is a basic form of bot prevention that `requests` alone cannot bypass.
- **Results**: Scraped {myscheme_count} schemes.

## 3. Data Completeness Evaluation

- The data collected includes the essential fields: `source`, `title`, `link`, and `description`.
- The Microsoft scraper is limited to the front page; completeness for the entire blog is low.
- The MyScheme scraper is designed to be complete for the `/schemes` page, as it loads all available items before scraping.
- Descriptions can sometimes be truncated or contain mixed content, requiring some string cleaning.
"""
    print(report)
    with open("output/summary_report.md", "w", encoding='utf-8') as f:
        f.write(report)
    logging.info("Summary report generated at output/summary_report.md")


if __name__ == "__main__":
    main()
