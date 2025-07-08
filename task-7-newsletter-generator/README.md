# Task 7: Multi-Agent Newsletter Generator using LangChain

This project implements an automated multi-agent system that scrapes top Web3 news sources, summarizes the key stories, composes a newsletter, and pushes it to a Telegram channel.

## Architecture & Agentic Workflow

The system follows a sequential pipeline of specialized agents and processes:

1.  **Scraper**: The `scraper.py` module uses the `newspaper3k` library to fetch and parse articles from a predefined list of top Web3 news publications (CoinDesk, CoinTelegraph, etc.).

2.  **Deduplicator**: Before processing, the `main.py` script uses a TF-IDF vectorizer and cosine similarity to identify and remove articles with highly similar titles. This prevents reporting on the same story from multiple sources.

3.  **Summarizer Agent**: `agents.py` defines a `LangChain` chain powered by a GPT model. This agent receives the text of a single article and is prompted to act as an expert financial analyst, producing a concise, neutral summary.

4.  **Newsletter Composer Agent**: A second `LangChain` chain acts as the "chief editor". It takes the collection of individual summaries and is prompted to compose a cohesive, well-formatted newsletter with a catchy title, introduction, body, and conclusion, all in Markdown format suitable for Telegram.

5.  **Telegram Bot**: The `telegram_sender.py` utility uses the `python-telegram-bot` library to push the final, formatted newsletter to a specified Telegram channel or group.

6.  **Scheduler**: The entire process is automated using the `schedule` library. The `main.py` script orchestrates the workflow and can be configured to run at a specific time daily or at frequent intervals for testing and simulation.

## How to Run

### Prerequisites

-   Python 3.8+
-   An [OpenAI API Key](https://platform.openai.com/api-keys).
-   A [Telegram Bot Token](https://core.telegram.org/bots#how-do-i-create-a-bot) from BotFather.
-   A Telegram Channel or Group ID where the bot has permission to post.

### Steps

1.  **Navigate to the Directory**:
    ```bash
    cd task-7-newsletter-generator
    ```

2.  **Set Up Environment Variables**:
    a.  Create a `.env` file by copying the structure from the example:
        ```bash
        cp .env.example .env
        ```
    b.  Edit the `.env` file and add your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
    c.  Set your OpenAI API Key as an environment variable in your terminal. This is done to prevent accidentally committing your key.
        ```bash
        # On Linux/macOS
        export OPENAI_API_KEY='your-openai-api-key'

        # On Windows (Command Prompt)
        set OPENAI_API_KEY=your-openai-api-key
        ```

3.  **Install Dependencies**: Create a virtual environment (recommended) and install the packages.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

4.  **Configure for Simulation**: For the 2+ days simulation, ensure the `config.py` file is set to testing mode:
    ```python
    # in config.py
    SCHEDULE_MODE = 'testing' 
    TESTING_INTERVAL_MINUTES = 5 # Or your desired interval
    ```

5.  **Run the Generator**:
    ```bash
    python main.py
    ```
    -   The script will immediately run the job once on startup.
    -   After the initial run, it will follow the schedule defined in `config.py`.
    -   Monitor the terminal for logs.

6.  **Check the Output**:
    -   You should receive a message in your configured Telegram channel/group.
    -   A Markdown file with the newsletter content will be saved in the `output/` directory for each run (e.g., `output/newsletter_2023-10-27_15-30.md`).

## Deliverables Checklist

-   [x] **Scraper pipelines**: Implemented in `scraper.py`.
-   [x] **Newsletter samples (for 2 days)**: The script automatically saves each generated newsletter to the `output/` folder and can be run in a loop to simulate multiple days.
-   [x] **Code + Readme + Demo**: All code is provided, along with this `README.md`. A demo video would show the steps in "How to Run" and the final message appearing in Telegram.
-   [x] **Telegram group invite for testing**: The `TELEGRAM_CHAT_ID` can be set to a test group, and an invite link can be shared.
