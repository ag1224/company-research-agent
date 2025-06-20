import asyncio
import json
import logging
import os
import sys
from typing import List

# Add the parent directory to sys.path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from search_engines.tavily_search import (
    TavilySearchResult,
    get_major_competitors_async,
    get_major_customers_async,
    get_recent_news_async,
)
from third_party_api.apollo_organization_api import ApolloOrganizationAPI
from third_party_api.coresignal_multisource_api import CoreSignalMultiSourceAPI

# Configure logging for this module
logger = logging.getLogger(__name__)


class MultiSourceResearcher:
    """
    Multi-source company researcher that combines Apollo API and Tavily Search
    to generate comprehensive company reports using LLM processing.
    """

    def __init__(self, domain: str):
        """
        Initialize the multi-source researcher.

        Args:
            domain: Company domain for Apollo API (e.g., example.com)
        """
        self.domain = domain
        self.apollo_api = ApolloOrganizationAPI(domain)
        self.coresignal_api = CoreSignalMultiSourceAPI(website=domain)
        self.llm = ChatOpenAI(model="o3")
        self._company_name = None  # Will be set after fetching data

    @property
    def company_name(self) -> str:
        """Get the company name, extracting from domain if not yet set."""
        if self._company_name is None:
            # Default to domain name capitalized if not set from API data
            return self.domain.replace(".com", "").replace("www.", "").title()
        return self._company_name

    def _set_company_name_from_data(
        self, apollo_data: dict | None = None, coresignal_data: dict | None = None
    ):
        """Extract company name from API data."""
        if apollo_data and apollo_data.get("organization", {}).get("name"):
            self._company_name = apollo_data["organization"]["name"]
        elif coresignal_data and coresignal_data.get("company_name"):
            self._company_name = coresignal_data["company_name"]
        elif apollo_data and apollo_data.get("name"):
            self._company_name = apollo_data["name"]

    def load_company_schema(self):
        """
        Load the company research schema from the JSON file
        """
        schema_path = os.path.join(
            os.path.dirname(__file__), "../company_research_schema.json"
        )
        try:
            with open(schema_path, "r") as f:
                schema = json.load(f)
            return json.dumps(schema, indent=2)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Company research schema file not found at {schema_path}. Please ensure the schema file exists."
            )
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in schema file at {schema_path}: {e}", e.doc, e.pos
            )

    async def fetch_apollo_data(self) -> dict:
        """
        Fetch and format Apollo organization data.

        Returns:
            Tuple of (raw_apollo_data, formatted_apollo_data)
        """
        logger.info("Fetching data from Apollo API...")
        apollo_data = await asyncio.to_thread(
            self.apollo_api.organization_enrichment_api
        )
        return apollo_data

    async def fetch_coresignal_data(self) -> dict:
        """
        Fetch and format CoreSignel data.
        """
        logger.info("Fetching data from CoreSignel API...")
        coresignal_data = await asyncio.to_thread(
            self.coresignal_api.company_multi_source_enrich
        )
        return coresignal_data

    async def fetch_tavily_data(
        self,
    ) -> List[TavilySearchResult]:
        """
        Fetch Tavily search data concurrently.

        Returns:
            customers
        """
        logger.info("Fetching %s company data from Tavily Search...", self.company_name)
        # Run all Tavily searches concurrently for efficiency
        customers = await get_major_customers_async(self.company_name)
        return customers

    async def generate_llm_company_report(
        self,
        apollo_data: dict,
        coresignal_data: dict,
        customers: List[TavilySearchResult],
    ) -> str:
        """
        Generate LLM-powered company report using CoreSignel, Apollo and Tavily data.

        Args:
            apollo_data: Formatted Apollo API data
            coresignal_data: Formatted CoreSignel API data
            customers: List of customer search results

        Returns:
            Generated markdown report as string
        """
        logger.info("Generating LLM report...")

        news = ""
        company_updates = coresignal_data.get("company_updates", [])
        if company_updates:
            for i, update in enumerate(company_updates[:3], 1):
                news += f"### News Item {i}\n"
                news += f"**Date:** {update.get('date', 'No Date')}  \n"
                # news += "**Source:** LinkedIn Company Updates  \n"
                news += f"**Summary:** {update.get('description', 'No description available')[:500]}{'...' if len(update.get('description', '')) > 500 else ''}  \n"
                if update.get("reactions_count"):
                    news += f"**Engagement:** {update.get('reactions_count')} reactions"
                if update.get("comments_count"):
                    news += f", {update.get('comments_count')} comments"
                news += "\n\n"
        else:
            news += "No recent news items found.\n\n"

        # Extract all company updates - description
        all_company_updates = [
            update.get("description", "") for update in company_updates
        ]

        # Extract competitors
        competitors = coresignal_data.get("competitors", [])
        # sort competitors by similarity_score
        competitors.sort(key=lambda x: x.get("similarity_score") or 0, reverse=True)
        competitors = competitors[:5]

        prompt = f"""
        You are a research assistant specialized in company analysis. Generate a structured, human-readable markdown report for the company: {self.company_name} using the following data fields and data sources in json format.
        
        ## Data fields:
        Company Overview:
        - Company Name
        - Website
        - Description
        - Founded Year
        - Status
        - Type
        Industry and Market:
        - Industry
        - Keywords
        Location
        - HQ and other locations Address, City, State, Country
        Contact Details -  Emails, Phone no.
        Leadership & Key Executives:
        - Name, Title, LinkedIn Profile
        Employee Insights
        - Employee Count
        - Ratings
        - Employees by Location
        - Employees by Title
        - Employee Growth
        Financials:
        - Annual Revenue
        - Recent Financial Performance
        Funding and Ownership
        - Funding Rounds
        - Total Funding
        - Recent Funding
        - Private or Public
        - Investors
        Competitors:
        - Name
        - Revenue and total funding
        Recent News:
        - News Title
        - News Summary
        - News Date
        - Source URL
        Enterprise Customers
        Online Presence - Website, LinkedIn 
        - Links
        - Followers
        
        ## Data Sources:
        Coresignel API: {json.dumps(coresignal_data, indent=2)}
        Apollo API: {json.dumps(apollo_data, indent=2)}

        ## Major/Enterprise Customers (from Tavily)
        Data: {[c.model_dump() for c in customers]}
        ---

        Instructions:
        - Use only the provided data. Do not fabricate or add any information not present above.
        - For each section, if data is missing or empty, state "No relevant data found."
        - Remove duplicates and ensure each entry is unique.
        - Format the report in clear, well-structured markdown with the above sections. Each section should be a separate markdown heading.
        - **IMPORTANT** Mention sources for each sections. If it is a link create a markdown link. Mark N/A if no source is available.
        - Do not include any information not present in the provided data.
        - Extract the source url from the news item/corresponding company update description and add it to the news item.
        - For Tavily data, create a markdown link for the source url.
        - **VERY IMPORTANT: Do NOT include any emojis, special characters, or symbols (such as 👀, 🚀, ✅, 📊, etc.) in the report as they can cause PDF generation issues. Use only standard text, numbers, and basic punctuation.**

        """

        response = await self.llm.ainvoke([SystemMessage(content=prompt)])
        return str(response.content)

    async def research_company(self) -> dict:
        """
        Perform complete multi-source company research.

        Returns:
            Dictionary containing all research data and generated report
        """
        logger.info("Starting multi-source research for: %s", self.company_name)
        logger.info("Domain: %s", self.domain)

        # Fetch data from both sources concurrently
        apollo_task = self.fetch_apollo_data()
        tavily_task = self.fetch_tavily_data()
        coresignal_task = self.fetch_coresignal_data()

        # Wait for both data sources
        (
            (apollo_data),
            (customers),
            coresignal_data,
        ) = await asyncio.gather(apollo_task, tavily_task, coresignal_task)

        # Set company name from API data
        self._set_company_name_from_data(apollo_data, coresignal_data)

        # Generate the LLM report
        report = await self.generate_llm_company_report(
            apollo_data, coresignal_data, customers
        )

        logger.info("Multi-source research completed successfully")

        return {
            "company_name": self.company_name,
            "domain": self.domain,
            "report": report,
            "raw_data": {
                "apollo_data": apollo_data,
                "tavily_customers": [c.model_dump() for c in customers],
                "coresignal_data": coresignal_data,
                # "tavily_news": [n.model_dump() for n in news],
                # "tavily_competitors": [c.model_dump() for c in competitors],
            },
        }

    def save_report_to_file(self, report: str, results_dir: str | None = None) -> str:
        """
        Save the generated report to a markdown file.

        Args:
            report: The markdown report to save
            results_dir: Directory to save the report (optional)

        Returns:
            Path to the saved file
        """
        if results_dir is None:
            results_dir = os.path.join(os.path.dirname(__file__), "../results")

        os.makedirs(results_dir, exist_ok=True)

        report_path = os.path.join(
            results_dir, f"{self.company_name}_multi_source_research_report.md"
        )

        with open(report_path, "w") as f:
            f.write(report)

        logger.info("Report saved to: %s", report_path)
        return report_path


# Example usage
if __name__ == "__main__":

    async def main():
        researcher = MultiSourceResearcher("example.com")
        result = await researcher.research_company()
        researcher.save_report_to_file(result["report"])
        logger.info("Research completed for %s", result["company_name"])

    asyncio.run(main())
