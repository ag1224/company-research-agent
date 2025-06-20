import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


class ApolloOrganizationAPI:
    def __init__(self, domain: str):
        self.base_url = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/api/v1")
        api_key = os.getenv("APOLLO_API_KEY")
        if not api_key:
            raise ValueError("APOLLO_API_KEY not set in environment variables.")
        self.headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }
        self.domain = domain

    def organization_enrichment_api(self):
        # Check if response file already exists
        results_dir = os.path.join(
            os.path.dirname(__file__), "../results/third_party_api_response"
        )
        os.makedirs(results_dir, exist_ok=True)
        company_slug = self.domain.replace(".", "_").replace(" ", "_")
        file_path = os.path.join(
            results_dir, f"{company_slug}_apollo_api_response.json"
        )

        # If file exists, load and return the cached response
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    result = json.load(f)
                print(f"\n=== Loaded cached Apollo API response from {file_path} ===\n")
                return result
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading cached file {file_path}: {e}")
                print("Proceeding with fresh API call...")

        url = f"{self.base_url}/organizations/enrich?domain={self.domain}"
        response = requests.get(url, headers=self.headers)
        result = response.json()

        print("\n=== Apollo API Result ===\n")
        # print(json.dumps(result, indent=2))
        # save the result to a file

        with open(file_path, "w+") as f:
            json.dump(result, f, indent=2)

        return result

    # def load_company_schema(self):
    #     """
    #     Load the company research schema from the JSON file
    #     """
    #     schema_path = os.path.join(
    #         os.path.dirname(__file__), "../company_research_schema.json"
    #     )
    #     try:
    #         with open(schema_path, "r") as f:
    #             schema = json.load(f)
    #         return json.dumps(schema, indent=2)
    #     except FileNotFoundError:
    #         raise FileNotFoundError(
    #             f"Company research schema file not found at {schema_path}. Please ensure the schema file exists."
    #         )
    #     except json.JSONDecodeError as e:
    #         raise json.JSONDecodeError(
    #             f"Invalid JSON in schema file at {schema_path}: {e}", e.doc, e.pos
    #         )

    # def format_response(self, json_response) -> str:
    #     company_details_model = self.load_company_schema()

    #     llm = ChatOpenAI(model="gpt-4o-mini")
    #     response = llm.invoke(
    #         [
    #             SystemMessage(
    #                 content=f"""
    #                         You are a helpful assistant that formats json response to the company_details_model.

    #                         The company_details_model is as follows:
    #                         {company_details_model}

    #                         The json response is as follows:
    #                         {json_response}

    #                         **Important Formatting Requirements:**
    #                             - Format the results to match the nested JSON structure above.
    #                             - Mark unavailable information as \"Not Found\" or empty arrays/objects as appropriate.
    #                             - Ensure the output is easy to parse and ready for downstream processing.
    #                         """
    #             )
    #         ],
    #     )

    #     results_dir = os.path.join(
    #         os.path.dirname(__file__), "../results/third_party_api_response"
    #     )
    #     os.makedirs(results_dir, exist_ok=True)
    #     company_slug = self.domain.replace(".", "_").replace(" ", "_")
    #     output_path = os.path.join(
    #         results_dir, f"{company_slug}_apollo_api_formatted_response.json"
    #     )

    #     with open(output_path, "w+") as f:
    #         f.write(str(response.content))
    #     print(f"\n=== Apollo API transformed response saved to {output_path} ===\n")

    #     return str(response.content)


# Example usage:
if __name__ == "__main__":
    domain = "getfastr.com"
    apollo_api = ApolloOrganizationAPI(domain)
    result = apollo_api.organization_enrichment_api()
    # apollo_api.format_response(result)
