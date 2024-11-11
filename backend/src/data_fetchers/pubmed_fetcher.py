import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
import json
from time import sleep

class PubMedFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def fetch_pubmed_data(self, query: str, max_results: int = 5) -> str:
        """Fetch detailed article data from PubMed E-utilities"""
        try:
            # First, search for IDs
            esearch_url = f"{self.base_url}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "api_key": self.api_key,
                "retmode": "json"
            }

            search_response = requests.get(esearch_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()

            # Extract PMIDs
            pmids = search_data['esearchresult']['idlist']

            if not pmids:
                return {}

            sleep(0.5)  # Respect API rate limits

            # Second, fetch article details
            efetch_url = f"{self.base_url}efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "api_key": self.api_key
            }

            fetch_response = requests.get(efetch_url, params=fetch_params)
            fetch_response.raise_for_status()

            return fetch_response.text

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def parse_pubmed_articles(self, xml_content: str) -> List[Dict]:
        """Parse PubMed XML content and extract information"""
        if not xml_content:
            return []

        root = ET.fromstring(xml_content)
        articles = []

        for article in root.findall('.//PubmedArticle'):
            article_data = {}

            # Basic article information
            article_data['pmid'] = article.find('.//PMID').text if article.find('.//PMID') is not None else None
            article_data['title'] = article.find('.//ArticleTitle').text if article.find('.//ArticleTitle') is not None else None

            # Journal info
            journal = article.find('.//Journal')
            if journal is not None:
                article_data['journal'] = journal.find('.//Title').text if journal.find('.//Title') is not None else None

            # Publication date
            pub_date = article.find('.//PubDate')
            if pub_date is not None:
                year = pub_date.find('Year').text if pub_date.find('Year') is not None else None
                month = pub_date.find('Month').text if pub_date.find('Month') is not None else None
                article_data['publication_date'] = f"{year} {month}".strip() if year else None

            # Abstract
            abstract = article.find('.//Abstract/AbstractText')
            if abstract is not None:
                article_data['abstract'] = abstract.text

            # Keywords
            keywords = article.findall('.//Keyword')
            if keywords:
                article_data['keywords'] = [k.text for k in keywords]

            # Authors
            authors = article.findall('.//Author')
            if authors:
                article_data['authors'] = []
                for author in authors:
                    if author.find('LastName') is not None and author.find('ForeName') is not None:
                        author_name = f"{author.find('ForeName').text} {author.find('LastName').text}"
                        article_data['authors'].append(author_name)

            # DOI
            doi = article.find('.//ArticleId[@IdType="doi"]')
            if doi is not None:
                article_data['doi'] = doi.text

            articles.append(article_data)

        return articles

    def format_disease_summary(self, articles: List[Dict]) -> str:
        """Format the parsed articles into a readable summary"""
        summary = []

        for article in articles:
            summary.append("\n=== Article Summary ===")
            summary.append(f"Title: {article.get('title', 'N/A')}")
            summary.append(f"Authors: {', '.join(article.get('authors', ['N/A']))}")
            summary.append(f"Journal: {article.get('journal', 'N/A')}")
            summary.append(f"Publication Date: {article.get('publication_date', 'N/A')}")

            if article.get('keywords'):
                summary.append(f"Keywords: {', '.join(article.get('keywords', []))}")

            if article.get('abstract'):
                summary.append("\nAbstract:")
                summary.append(article.get('abstract'))

            summary.append(f"\nDOI: {article.get('doi', 'N/A')}")
            summary.append("\n")

        return "\n".join(summary)

    def fetch_and_summarize(self, query: str, max_results: int = 5) -> str:
        """Fetch PubMed data and return a formatted summary"""
        xml_content = self.fetch_pubmed_data(query, max_results)
        if xml_content:
            articles = self.parse_pubmed_articles(xml_content)
            return self.format_disease_summary(articles)
        return "No results found or error occurred"