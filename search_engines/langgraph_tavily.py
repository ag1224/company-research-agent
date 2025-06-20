import os
from typing import List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

load_dotenv()


# Define the state structure
class ResearchState(TypedDict):
    company: str
    news: Optional[List[dict]]
    customers: Optional[List[dict]]
    relevant: Optional[bool]
    relevance_reason: Optional[str]


# Initialize tools

tavily_tool = TavilySearchResults(max_results=5)
llm = ChatOpenAI(model="gpt-4o")


def search_news(state: ResearchState) -> dict:
    """Search for recent company news"""
    query = f"Recent news about {state['company']} from the last 6 months"
    results = tavily_tool.invoke(
        {
            "query": query,
            "topic": "news",
            "search_depth": "advanced",
        }
    )
    print(results)
    return {"news": results}


def search_customers(state: ResearchState) -> dict:
    """Search for major company customers"""
    query = f"Major customers of {state['company']}"
    results = tavily_tool.invoke({"query": query, "search_depth": "advanced"})
    return {"customers": results}


def check_relevance(state: ResearchState) -> dict:
    """Verify information relevance to the company"""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You're a corporate research specialist. Determine if the collected information is truly about {company}.",
            ),
            (
                "human",
                "Verify relevance based on:\n"
                "1. News: {news}\n"
                "2. Customers: {customers}\n\n"
                "Check for:\n"
                "- Direct mentions of {company}\n"
                "- Contextual relevance\n"
                "- Potential confusion with similar names\n\n"
                "Format response:\n"
                "REASON: <explanation>\n"
                "VERDICT: <True/False>",
            ),
        ]
    )

    news_str = (
        "\n".join(
            [
                f"- {res['title']} ({res['url']})\nContent: {res['content']}\n"
                for res in (state.get("news") or [])
            ]
        )
        if state.get("news")
        else "No news found"
    )
    customers_str = (
        "\n".join(
            [
                f"- {res['title']} ({res['url']})\nContent: {res['content']}\n"
                for res in (state.get("customers") or [])
            ]
        )
        if state.get("customers")
        else "No customers found"
    )

    chain = prompt | llm
    response = chain.invoke(
        {"company": state["company"], "news": news_str, "customers": customers_str}
    )

    # Parse response
    reason = str(response.content).split("REASON:")[-1].split("VERDICT:")[0].strip()
    verdict = "True" in str(response.content).split("VERDICT:")[-1].strip()

    return {"relevant": verdict, "relevance_reason": reason}


# Build the workflow
workflow = StateGraph(ResearchState)

# Add nodes
workflow.add_node("search_news", search_news)
workflow.add_node("search_customers", search_customers)
workflow.add_node("check_relevance", check_relevance)

# Set entry point
workflow.set_entry_point("search_news")

# Connect nodes
workflow.add_edge("search_news", "search_customers")
workflow.add_edge("search_customers", "check_relevance")
workflow.add_edge("check_relevance", END)

# Compile the graph
research_agent = workflow.compile()

# Example usage
if __name__ == "__main__":
    results = research_agent.invoke(
        {
            "company": "getfastr.com",
            "news": None,
            "customers": None,
            "relevant": None,
            "relevance_reason": None,
        }
    )

    # print("\n--- RESEARCH RESULTS ---")
    # print(f"Company: {results['company']}")
    # print(f"Relevance Verified: {results['relevant']}")
    # print(f"Relevance Reason: {results['relevance_reason']}")

    # print("\nTop News:")
    # for i, news_item in enumerate(results["news"][:3], 1):
    #     print(f"{i}. {news_item['title']} ({news_item['url']})")
    #     if "content" in news_item and news_item["content"]:
    #         print(f"   Content: {news_item['content'][:200]}...")

    # if results["customers"]:
    #     print("\nMajor Customers:")
    #     for i, customer in enumerate(results["customers"][:5], 1):
    #         print(f"{i}. {customer['title']}")
    #         if "content" in customer and customer["content"]:
    #             print(f"   Content: {customer['content'][:200]}...")

    # --- Write structured report to file ---
    os.makedirs("results", exist_ok=True)
    company_slug = results["company"].replace(".", "_").replace(" ", "_")
    report_path = f"results/{company_slug}_customers_and_news_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Company Research Report: {results['company']}\n\n")
        f.write(f"**Relevance Verified:** {results['relevant']}\n\n")
        f.write(f"**Relevance Reason:** {results['relevance_reason']}\n\n")
        f.write("## Top News\n")
        if results["news"]:
            for i, news_item in enumerate(results["news"][:3], 1):
                f.write(f"{i}. [{news_item['title']}]({news_item['url']})\n\n")
                if "content" in news_item and news_item["content"]:
                    snippet = news_item["content"][:500].replace("\n", " ")
                    f.write(f"   - Content: {snippet}...\n\n")
        else:
            f.write("No news found.\n\n")
        f.write("## Major Customers\n")
        if results["customers"]:
            for i, customer in enumerate(results["customers"][:5], 1):
                f.write(f"{i}. {customer['title']}\n\n")
                if "content" in customer and customer["content"]:
                    snippet = customer["content"][:500].replace("\n", " ")
                    f.write(f"   - Content: {snippet}...\n\n")
        else:
            f.write("No major customers found.\n\n")
    print(f"\nReport written to {report_path}\n")
