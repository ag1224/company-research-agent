import asyncio
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tavily import AsyncTavilyClient

load_dotenv()


class TavilySearchResult(BaseModel):
    """Schema for Tavily search result items."""

    url: str
    title: str
    score: float
    published_date: Optional[str] = None
    content: Optional[str] = None


def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in environment variables.")
    return AsyncTavilyClient(api_key=api_key)


async def get_major_customers_async(company_name: str) -> list[TavilySearchResult]:
    query = f"Who are the major/enterprise customers of {company_name}?"
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = AsyncTavilyClient(api_key=api_key)
    response = await tavily_client.search(
        query,
        max_results=5,
        search_depth="advanced",
    )
    results = response.get("results", [])
    print("\n===Major customers (async)===\n")
    # print(results)
    return [TavilySearchResult(**r) for r in results if r]


async def get_recent_news_async(company_name: str) -> list[TavilySearchResult]:
    query = f"Recent news about {company_name}"
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = AsyncTavilyClient(api_key=api_key)
    response = await tavily_client.search(
        query, max_results=3, topic="news", days=365, search_depth="advanced"
    )
    results = response.get("results", [])
    print("\n===Recent news (async)===\n")
    # print(results)
    return [TavilySearchResult(**r) for r in results if r]


async def get_major_competitors_async(company_name: str) -> list[TavilySearchResult]:
    query = f"Who are the major competitors of {company_name}?"
    api_key = os.getenv("TAVILY_API_KEY")
    tavily_client = AsyncTavilyClient(api_key=api_key)
    response = await tavily_client.search(
        query,
        max_results=5,
        search_depth="advanced",
    )
    results = response.get("results", [])
    print("\n===Major competitors (async)===\n")
    # print(results)
    return [TavilySearchResult(**r) for r in results if r]


def format_tavily_results(results: list[TavilySearchResult], section: str) -> str:
    if not results:
        return "No relevant data found"
    lines = []
    for r in results:
        summary = r.content or "No summary available."
        title = r.title or "No title."
        url = r.url or "No URL."
        date = f" (Published: {r.published_date})" if r.published_date else ""
        if section == "news":
            lines.append(f"- **{title}**{date}: {summary} [Source]({url})")
        else:
            lines.append(f"- **{title}**: {summary} [Source]({url})")
    formatted_results = "\n".join(lines)
    print(f"\n===Formatted {section}===\n")
    print(formatted_results)
    return formatted_results


async def run_company_major_customers_and_news_agent_async(company_name: str):
    model = ChatOpenAI(model="gpt-4o")

    # Gather data
    recent_news = await get_recent_news_async(company_name)
    major_customers = await get_major_customers_async(company_name)
    major_competitors = await get_major_competitors_async(company_name)

    # Format data for prompt
    formatted_news = format_tavily_results(recent_news, section="news")
    formatted_customers = format_tavily_results(major_customers, section="customers")
    formatted_competitors = format_tavily_results(
        major_competitors, section="competitors"
    )

    report = model.invoke(
        [
            SystemMessage(
                content=f"""
You are a research assistant specialized in company analysis. 
Your task is to generate a structured, human-readable markdown report for the company: {company_name}.

You are provided with three lists:
- Major or enterprise customers (3-5 items)
- Recent news headlines or summaries about the company from the last 1 year (0-3 items)
- Major competitors (3-5 items)

The data for these lists is provided below. 
**Only use the information from these lists. Do not fabricate or add any information not present in the lists.**

---
### Data Provided

**Recent news:**
{formatted_news}

**Major customers:**
{formatted_customers}

**Major competitors:**
{formatted_competitors}

---

### Instructions

- Only include news, customers, and competitors that are directly relevant to the company. Exclude generic, unrelated, or ambiguous entries.
- **Important** For each item use bullet points, include a summary, title and a source URL (labelled as 'Source').
- If any list is empty or contains only irrelevant items, state "No relevant data found" for that section.
- Remove duplicates and ensure each entry is unique.
- Format the report in clear, well-structured markdown with the following sections:
    - # {company_name} Research Report
    - ## Major/Enterprise Customers
    - ## Recent News
    - ## Major Competitors
- For news, include the headline, a brief summary, the published date (if available), and the source URL.
- Do not include any information not present in the provided lists.

---

Generate the markdown report below:
"""
            )
        ]
    )
    # Save to file
    results_dir = os.path.join(os.path.dirname(__file__), "../results")
    os.makedirs(results_dir, exist_ok=True)
    company_slug = company_name.replace(".", "_").replace(" ", "_")
    output_path = os.path.join(results_dir, f"{company_slug}_tavily_research.md")
    with open(output_path, "w+") as f:
        f.write(str(report.content))
    print(f"\nReport written to {output_path}\n")


if __name__ == "__main__":
    asyncio.run(
        run_company_major_customers_and_news_agent_async("getfastr.com (Zmags)")
    )
