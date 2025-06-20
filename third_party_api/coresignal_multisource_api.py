import json
import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv()


class CoreSignalMultiSourceAPI:
    def __init__(self, website: str):
        self.base_url = os.getenv("CORESIGNAL_BASE_URL", "https://api.coresignal.com")
        api_key = os.getenv("CORESIGNAL_API_KEY")
        if not api_key:
            raise ValueError("CORESIGNAL_API_KEY not set in environment variables.")
        self.headers = {
            "accept": "application/json",
            "apikey": api_key,
        }
        self.website = website
        self.website_slug = (
            self.website.replace("https://", "")
            .replace("http://", "")
            .replace("www.", "")
            .replace(".", "_")
            .replace("/", "_")
        )

    def company_multi_source_enrich(self):
        """
        Enrich company data using CoreSignal's multi-source API
        """
        # Check if response file already exists
        results_dir = os.path.join(
            os.path.dirname(__file__), "../results/third_party_api_response"
        )
        file_path = os.path.join(
            results_dir,
            f"{self.website_slug}_coresignal_multisource_api_response.json",
        )

        # If file exists, load and return the cached response
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    result = json.load(f)
                print(
                    f"\n=== Loaded cached CoreSignal API response from {file_path} ===\n"
                )
                return result
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading cached file {file_path}: {e}")
                print("Proceeding with fresh API call...")

        # URL encode the website parameter
        encoded_website = quote(self.website, safe="")
        url = f"{self.base_url}/cdapi/v2/company_multi_source/enrich?website={encoded_website}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            # print(json.dumps(result, indent=2))
            # save to file
            os.makedirs(results_dir, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n=== CoreSignal API response saved to {file_path} ===\n")
            return result

        except Exception as e:
            print(f"An error occurred: {e}")
            raise

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

    def generate_markdown_report(self, api_response: dict) -> str:
        """
        Generate a structured markdown report with specific company information
        """
        company_name = api_response.get("company_name", "Unknown Company")

        markdown_report = f"""# {company_name} - Company Research Report

## Company Industry Type & Description

**Industry:** {api_response.get("industry", "Not Found")}  
**Company Type:** {api_response.get("type", "Not Found")}  
**Status:** {api_response.get("status", {}).get("value", "Not Found")}  

### Description
{api_response.get("description", "Not Found")}

## Contact Details

### Address
**Headquarters:** {api_response.get("hq_location", "Not Found")}  
**Full Address:** {api_response.get("hq_full_address", "Not Found")}  

### CEO Profile
"""

        # Extract CEO information from employees data
        employees = api_response.get("employees", [])
        ceo_found = False
        for employee in employees:
            job_title = employee.get("job_title", "").lower()
            if any(
                title in job_title
                for title in ["ceo", "chief executive officer", "founder"]
            ):
                markdown_report += f"""**Name:** {employee.get("full_name", "Not Found")}  
**Title:** {employee.get("job_title", "Not Found")}  
**LinkedIn:** {employee.get("linkedin_url", "Not Found")}  
**Start Date:** {employee.get("job_start_date", "Not Found")}  
"""
                ceo_found = True
                break

        if not ceo_found:
            markdown_report += "CEO information not found.\n"

        markdown_report += f"""

## Website and LinkedIn Page

**Website:** {api_response.get("website", "Not Found")}  
**LinkedIn Company Page:** {api_response.get("linkedin_url", "Not Found")}  
**LinkedIn Followers:** {api_response.get("followers_count_linkedin", "Not Found"):,} followers  

## Employee Count

**Current Employee Count:** {api_response.get("employees_count", "Not Found")}  
**Size Range:** {api_response.get("size_range", "Not Found")}  

### Geographic Distribution
"""

        # Add employee distribution by country
        employee_history = api_response.get("employees_count_history", [])
        if employee_history:
            latest_data = employee_history[0]
            employees_by_country = latest_data.get("employees_count_by_country", [])
            for country_data in employees_by_country:
                markdown_report += f"- **{country_data.get('country', 'Unknown')}:** {country_data.get('employee_count', 0)} employees\n"
        else:
            markdown_report += "Geographic distribution data not available.\n"

        markdown_report += """

## Financing/Funding & Type

"""

        # Look for funding information in the API response
        # CoreSignal API might have funding data in different fields
        funding_info = api_response.get("funding_info", {})
        if funding_info:
            markdown_report += f"**Total Funding:** {funding_info.get('total_amount', 'Not Found')}  \n"
            markdown_report += (
                f"**Funding Type:** {funding_info.get('type', 'Not Found')}  \n"
            )
            markdown_report += f"**Number of Rounds:** {funding_info.get('rounds_count', 'Not Found')}  \n"
        else:
            # Check for acquisition or investment status
            status_comment = api_response.get("status", {}).get("comment", "")
            if "acquired" in status_comment.lower():
                markdown_report += "**Status:** Acquired  \n"
            else:
                markdown_report += (
                    "Funding information not available in current data source.\n"
                )

        markdown_report += """

## 3 Recent News Items

"""

        # Extract recent company updates as news
        company_updates = api_response.get("company_updates", [])
        if company_updates:
            for i, update in enumerate(company_updates[:3], 1):
                markdown_report += f"### News Item {i}\n"
                markdown_report += f"**Date:** {update.get('date', 'No Date')}  \n"
                markdown_report += "**Source:** LinkedIn Company Updates  \n"
                markdown_report += f"**Summary:** {update.get('description', 'No description available')[:200]}{'...' if len(update.get('description', '')) > 200 else ''}  \n"
                if update.get("reactions_count"):
                    markdown_report += (
                        f"**Engagement:** {update.get('reactions_count')} reactions"
                    )
                if update.get("comments_count"):
                    markdown_report += f", {update.get('comments_count')} comments"
                markdown_report += "\n\n"
        else:
            markdown_report += "No recent news items found.\n\n"

        markdown_report += """## Enterprise Customers

"""

        # Look for customer information
        customers = api_response.get("customers", [])
        enterprise_customers = api_response.get("enterprise_customers", [])

        if customers or enterprise_customers:
            all_customers = customers + enterprise_customers
            for customer in all_customers[:5]:  # Show top 5
                markdown_report += f"- **{customer.get('name', 'Unknown Customer')}**"
                if customer.get("industry"):
                    markdown_report += f" - {customer.get('industry')}"
                if customer.get("website"):
                    markdown_report += f" - {customer.get('website')}"
                markdown_report += "\n"
        else:
            markdown_report += "Enterprise customer information not available in current data source.\n"

        markdown_report += """

## Competition & Basic Description

"""

        # Look for competitor information
        competitors = api_response.get("competitors", [])
        competition = api_response.get("competition", [])

        if competitors or competition:
            all_competitors = competitors + competition
            for competitor in all_competitors[:5]:  # Show top 5
                markdown_report += (
                    f"### {competitor.get('name', 'Unknown Competitor')}\n"
                )
                if competitor.get("description"):
                    markdown_report += f"{competitor.get('description')}\n"
                if competitor.get("website"):
                    markdown_report += f"**Website:** {competitor.get('website')}  \n"
                if competitor.get("industry"):
                    markdown_report += f"**Industry:** {competitor.get('industry')}  \n"
                markdown_report += "\n"
        else:
            # Use industry keywords to suggest potential competitors
            keywords = api_response.get("categories_and_keywords", [])
            markdown_report += "Direct competitor information not available. Based on industry keywords, potential competitors may include companies in:\n"
            for keyword in keywords[:5]:
                if any(
                    term in keyword.lower()
                    for term in ["software", "technology", "platform", "solution"]
                ):
                    markdown_report += f"- {keyword}\n"

        markdown_report += f"""

---

**Data Source:** CoreSignal Multi-Source API  
**Last Updated:** {api_response.get("last_updated_at", "Not Found")}  
**Report Generated:** {json.dumps({"timestamp": "auto-generated"})}

*This report was generated automatically from available data sources. Some information may be limited based on data availability.*
"""

        return markdown_report

    def generate_markdown_report_with_llm(self, api_response: dict) -> str:
        model = ChatOpenAI(model="gpt-4o")

        # Extract recent company updates as news
        news = ""
        company_updates = api_response.get("company_updates", [])
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
        competitors = api_response.get("competitors", [])
        # sort competitors by similarity_score
        competitors.sort(key=lambda x: x.get("similarity_score") or 0, reverse=True)
        competitors = competitors[:5]

        prompt = f"""
        You are a research assistant specialized in company analysis. Generate a structured, human-readable markdown report for the company: {
            self.website
        } using the following data fields.
        
        ## Data fields:
        {self.load_company_schema()}
        Recent news --> {news}
        Funding --> last_funding_round, funding_rounds
        Competitors --> {competitors}
        Company Updates for Customer Analysis --> {all_company_updates}
        
        Coresignal data:
        {json.dumps(api_response, indent=2)}

        Instructions:
        - Use only the provided data. Do not fabricate or add any information not present above.
        - For each section, if data is missing or empty, state "No relevant data found."
        - Remove duplicates and ensure each entry is unique.
        - Format the report in clear, well-structured markdown with the above sections.
        - Extract the source url from the news item/corresponding company update description and add it to the news item.
        - **VERY IMPORTANT: Do NOT include any emojis, special characters, or symbols (such as 👀, 🚀, ✅, 📊, etc.) in the report as they can cause PDF generation issues. Use only standard text, numbers, and basic punctuation.**
        - For Enterprise Customers section: Carefully analyze the company updates to infer potential customers and clients by looking for:
          * Direct mentions of company names as clients, customers, or partners
          * Success stories or case studies mentioning specific organizations
          * Announcements about new partnerships, collaborations, or deals
          * Posts celebrating client wins, implementations, or go-lives
          * Thank you messages or shout-outs to specific companies
          * Event participation or speaking engagements with other organizations
          * Product launches or feature announcements mentioning specific users/companies
        - Look for linguistic patterns like: "partnership with [Company]", "client [Company]", "working with [Company]", "proud to announce [Company]", "congratulations to [Company]", "[Company] is now using", "implementation at [Company]"
        - Extract company names from these contexts and list them as potential enterprise customers
        - If no clear customer mentions are found in updates, state "No customer information could be inferred from available company updates"
        """

        response = model.invoke([SystemMessage(content=prompt)])
        return str(response.content)


# Example usage:
if __name__ == "__main__":
    website = "https://www.jrni.com"
    coresignal_api = CoreSignalMultiSourceAPI(website)

    # Get API data
    api_response = coresignal_api.company_multi_source_enrich()

    # Generate comprehensive reports
    results_dir = os.path.join(os.path.dirname(__file__), "../results")
    os.makedirs(results_dir, exist_ok=True)

    # Generate markdown report
    markdown_report = coresignal_api.generate_markdown_report_with_llm(api_response)
    markdown_path = os.path.join(
        results_dir, f"{coresignal_api.website_slug}_coresignal_report.md"
    )
    with open(markdown_path, "w") as f:
        f.write(markdown_report)

    print("\n=== Company Report Generated ===")
    print(f"Markdown Report: {markdown_path}")

    # Format response using LLM (legacy method)
    # formatted_result = coresignal_api.format_response(result)
    # print("\n=== Formatted Result ===\n")
    # print(formatted_result)
