import requests
import json
from typing import List, Dict
import textwrap

class NIHFetcher:
    def __init__(self):
        self.base_url = "https://api.reporter.nih.gov/v2/projects/search"

    def format_currency(self, amount: float) -> str:
        """Format currency with appropriate suffix for large numbers"""
        if amount >= 1_000_000:
            return f"${amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.1f}K"
        else:
            return f"${amount:.2f}"

    def fetch_nih_reporter(self, search_term: str, limit: int = 5) -> dict:
        """Fetch rare disease research data from NIH RePORTER"""
        try:
            payload = {
                "criteria": {
                    "text_search_criteria": [{
                        "search_field": "all",
                        "search_text": search_term
                    }],
                    "fiscal_years": [2024, 2023, 2022, 2021, 2020]  # Last 5 years
                },
                "include_fields": [
                    "fiscal_year",
                    "award_amount",
                    "project_title",
                    "abstract_text",
                    "ContactPIName",
                    "OrganizationName"
                ],
                "offset": 0,
                "limit": limit,
                "sort_field": "fiscal_year",
                "sort_order": "desc"
            }

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error accessing NIH RePORTER API: {e}")
            return None

    def parse_nih_projects(self, response_data: dict) -> List[Dict]:
        """Parse NIH RePORTER response and extract relevant project information"""
        if not response_data or 'results' not in response_data:
            return []

        projects = []
        for result in response_data['results']:
            project = {
                'title': result.get('project_title'),
                'pi_name': result.get('contact_pi_name'),
                'organization': result.get('organization_name'),
                'abstract': result.get('abstract_text', '').strip(),
                'award_amount': float(result.get('award_amount', 0)),
                'fiscal_year': result.get('fiscal_year'),
                'formatted_amount': self.format_currency(float(result.get('award_amount', 0)))
            }
            projects.append(project)

        return projects

    def format_nih_summary(self, projects: List[Dict], meta: dict) -> str:
        """Format the parsed NIH project data into a readable summary"""
        if not projects:
            return "No projects found matching the search criteria."

        summary = []
        total_results = meta.get('total', 0)

        summary.append("=== NIH Rare Disease Research Projects ===")
        summary.append(f"Database Total: {total_results:,} projects")
        summary.append(f"Showing: Latest {len(projects)} projects\n")

        total_funding = sum(p['award_amount'] for p in projects)

        for i, project in enumerate(projects, 1):
            summary.append(f"Project {i} | FY{project['fiscal_year']} | {project['formatted_amount']}")
            summary.append("-" * 65)

            title = textwrap.fill(project['title'] or "No Title Available", width=65)
            summary.append(title)

            summary.append(f"\nPI: {project['pi_name'] or 'Not Available'}")
            summary.append(f"Institution: {project['organization'] or 'Not Available'}")

            if project['abstract']:
                abstract_preview = project['abstract'][:200] + "..." if len(project['abstract']) > 200 else project['abstract']
                wrapped_abstract = textwrap.fill(abstract_preview, width=65,
                                               initial_indent='  ',
                                               subsequent_indent='  ')
                summary.append(f"\nAbstract Preview:")
                summary.append(wrapped_abstract)

            summary.append("\n" + "-" * 65 + "\n")

        if projects:
            avg_funding = total_funding / len(projects)
            summary.append("Funding Overview")
            summary.append("-" * 15)
            summary.append(f"Total Funding: {self.format_currency(total_funding)}")
            summary.append(f"Average Award: {self.format_currency(avg_funding)}")
            summary.append(f"Largest Award: {self.format_currency(max(p['award_amount'] for p in projects))}")
            if any(p['fiscal_year'] for p in projects):
                summary.append(f"Latest Fiscal Year: {max(p['fiscal_year'] for p in projects)}")

        return "\n".join(summary)

    def fetch_and_summarize_nih_projects(self, search_term: str = "rare diseases",
                                       limit: int = 5) -> str:
        """Fetch NIH project data and return a formatted summary"""
        response_data = self.fetch_nih_reporter(search_term, limit)
        if response_data:
            projects = self.parse_nih_projects(response_data)
            return self.format_nih_summary(projects, response_data.get('meta', {}))
        return "Failed to fetch data from NIH RePORTER API"