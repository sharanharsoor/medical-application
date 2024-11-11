import requests
from typing import List, Dict
from datetime import datetime
import re

class MedRxivFetcher:
    def __init__(self):
        self.base_url = "https://api.biorxiv.org/details/medrxiv"

    def fetch_medrxiv_data(self, start_date: str = "2024-01-01",
                          end_date: str = "2024-12-31",
                          cursor: int = 0) -> dict:
        """Fetch data from MedRxiv/BioRxiv API"""
        try:
            url = f"{self.base_url}/{start_date}/{end_date}/{cursor}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def is_rare_disease_paper(self, paper: Dict) -> bool:
        """Check if a paper is related to rare diseases"""
        rare_disease_keywords = [
            'rare disease', 'rare disorder', 'orphan disease', 'rare genetic',
            'rare mutation', 'rare syndrome', 'rare condition',
            'ultra-rare', 'rare inherited', 'rare metabolic'
        ]

        text_to_search = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        return any(keyword.lower() in text_to_search for keyword in rare_disease_keywords)

    def parse_medrxiv_papers(self, response_data: dict) -> List[Dict]:
        """Parse MedRxiv JSON response and extract rare disease related papers"""
        if not response_data or 'collection' not in response_data:
            return []

        rare_disease_papers = []

        for paper in response_data['collection']:
            if self.is_rare_disease_paper(paper):
                paper_data = {
                    'title': paper.get('title'),
                    'doi': paper.get('doi'),
                    'authors': paper.get('authors'),
                    'date': paper.get('date'),
                    'category': paper.get('category'),
                    'abstract': paper.get('abstract'),
                    'institution': paper.get('author_corresponding_institution'),
                    'corresponding_author': paper.get('author_corresponding')
                }
                rare_disease_papers.append(paper_data)

        return rare_disease_papers

    def format_paper_summary(self, papers: List[Dict]) -> str:
        """Format the parsed papers into a readable summary"""
        if not papers:
            return "No rare disease related papers found in the specified time period."

        summary = []
        summary.append(f"\n=== Rare Disease Research Papers (Total: {len(papers)}) ===\n")

        for i, paper in enumerate(papers, 1):
            summary.append(f"Paper {i}:")
            summary.append("-" * 50)
            summary.append(f"Title: {paper.get('title', 'N/A')}")
            summary.append(f"Authors: {paper.get('authors', 'N/A')}")
            summary.append(f"Date: {paper.get('date', 'N/A')}")
            summary.append(f"Category: {paper.get('category', 'N/A')}")
            summary.append(f"Institution: {paper.get('institution', 'N/A')}")
            summary.append(f"DOI: {paper.get('doi', 'N/A')}")

            if paper.get('abstract'):
                summary.append("\nAbstract:")
                # Word wrap abstract
                words = paper['abstract'].split()
                lines = []
                current_line = []
                line_length = 0

                for word in words:
                    if line_length + len(word) + 1 <= 80:
                        current_line.append(word)
                        line_length += len(word) + 1
                    else:
                        lines.append(" ".join(current_line))
                        current_line = [word]
                        line_length = len(word)

                if current_line:
                    lines.append(" ".join(current_line))

                summary.extend(lines)

            summary.append("\n" + "=" * 80 + "\n")

        return "\n".join(summary)

    def fetch_and_summarize_rare_disease_papers(self,
                                              start_date: str = "2024-01-01",
                                              end_date: str = "2024-12-31") -> str:
        """Fetch MedRxiv data and return a formatted summary of rare disease papers"""
        response_data = self.fetch_medrxiv_data(start_date, end_date)
        if response_data:
            papers = self.parse_medrxiv_papers(response_data)
            return self.format_paper_summary(papers)
        return "Failed to fetch data from MedRxiv API"