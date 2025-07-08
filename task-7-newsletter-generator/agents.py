from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict
import logging
import tiktoken

from config import LLM_MODEL_NAME

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper function to truncate text ---
def truncate_text(text: str, max_tokens: int) -> str:
    """Truncates text to a maximum number of tokens."""
    try:
        encoding = tiktoken.encoding_for_model(LLM_MODEL_NAME)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return text

# --- LangChain Agent/Chain Definitions ---
def get_summarizer_chain() -> LLMChain:
    """
    Creates a LangChain chain that summarizes an article.
    """
    llm = ChatOpenAI(temperature=0.0, model_name=LLM_MODEL_NAME)
    
    prompt_template = """
    You are an expert financial news analyst specializing in the Web3 and cryptocurrency space.
    Your task is to provide a clear, concise, and neutral one-paragraph summary of the following article.
    Focus on the key information, impact, and main takeaways.

    ARTICLE TEXT:
    ---
    {article_text}
    ---

    SUMMARY:
    """
    
    prompt = PromptTemplate(
        input_variables=["article_text"],
        template=prompt_template
    )
    
    return LLMChain(llm=llm, prompt=prompt)

def get_newsletter_composer_chain() -> LLMChain:
    """
    Creates a LangChain chain to compose a full newsletter from a list of article summaries.
    """
    llm = ChatOpenAI(temperature=0.7, model_name=LLM_MODEL_NAME) # Higher temp for creativity
    
    prompt_template = """
    You are the chief editor of "Web3 Daily Digest," a popular Telegram newsletter.
    Your tone is professional, insightful, and slightly informal to engage the reader.
    
    Your task is to compose today's newsletter using the provided article summaries.
    
    GUIDELINES:
    1.  **Header**: Create a catchy, relevant title for the newsletter, starting with an emoji (e.g., "🚀 Web3 Daily Digest: ...").
    2.  **Introduction**: Write a brief (2-3 sentence) intro that sets the stage for the day's news. Mention the top themes.
    3.  **Body**:
        -   Format each story clearly with a bold title.
        -   Use the provided summary for the content.
        -   Include the source name and a link to the original article in this format: `(Source: [Source Name](URL))`.
        -   Use Markdown for formatting (e.g., *bold*, _italics_). Add relevant emojis to headlines.
    4.  **Footer**: Write a short, engaging conclusion, perhaps with a forward-looking statement or a call to action (e.g., "Stay tuned for more!").
    5.  The final output must be a single block of text, fully formatted with Markdown and ready to be sent to Telegram.

    Here are today's article summaries:
    ---
    {summaries}
    ---
    
    Compose the newsletter now.
    """
    
    prompt = PromptTemplate(input_variables=["summaries"], template=prompt_template)
    
    return LLMChain(llm=llm, prompt=prompt)

def summarize_article(article: Dict, summarizer_chain: LLMChain) -> str:
    """
    Summarizes a single article using the provided summarizer chain.
    Truncates article text to avoid exceeding token limits.
    """
    logging.info(f"Summarizing article: {article['title']}")
    
    # Truncate text to fit within context window (e.g., 3000 tokens for summary)
    truncated_text = truncate_text(article['text'], max_tokens=3000)
    
    try:
        result = summarizer_chain.invoke({"article_text": truncated_text})
        summary = result['text'].strip()
        return summary
    except Exception as e:
        logging.error(f"Failed to summarize article {article['title']}: {e}")
        return "Could not generate summary for this article."
