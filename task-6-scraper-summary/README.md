# Task 6: Article + Scheme Scraper & Summary Report

This project contains a Python script to scrape data from two websites: one static (Microsoft Research Blog) and one dynamic (MyScheme Portal).

## Architecture

-   **Static Scraper (Microsoft Research Blog)**: Uses the `requests` library to fetch the HTML and `BeautifulSoup4` to parse it. This is efficient for sites that do not rely on JavaScript to render content.
-   **Dynamic Scraper (MyScheme Portal)**: Uses `Playwright` to control a headless browser (Chromium). This is necessary to render the page's JavaScript, handle user interactions like clicking a "Load More" button, and scrape the fully-rendered content.
-   **Data Storage**: The scraped data from both sources is combined and saved into a structured format in the `output/` directory as `scraped_data.csv` and `scraped_data.json`.
-   **Reporting**: A detailed summary report is generated and printed to the console, and also saved as `output/summary_report.md`. This report covers the challenges, architectural decisions, and an evaluation of data completeness for each scraper.

## How to Run

### Prerequisites

-   Python 3.8+
-   Pip

### Steps

1.  **Navigate to the Directory**:
    ```bash
    cd task-6-scraper-summary
    ```

2.  **Install Dependencies**: Create a virtual environment (recommended) and install the required packages.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
    
3.  **Install Playwright Browsers**: The scraper script will automatically run the command to install the necessary browser binaries for Playwright, but you can also do it manually beforehand:
    ```bash
    playwright install
    ```

4.  **Run the Scraper**:
    ```bash
    python scraper.py
    ```

5.  **Check the Output**:
    -   The script will log its progress in the terminal.
    -   At the end, it will print the full summary report.
    -   The scraped data will be available in the `output/` directory as `scraped_data.csv` and `scraped_data.json`.
    -   The summary report will also be saved in `output/summary_report.md`.

## Deliverables Checklist

-   [x] **Scraper Code**: `scraper.py` contains the logic for both scrapers.
-   [x] **Exported Dataset**: The script generates `scraped_data.csv` and `scraped_data.json` in the `output` folder.
-   [x] **Summary + Demo Video**: The script generates `summary_report.md`. A demo video would show the execution of the script and the contents of the output files.
