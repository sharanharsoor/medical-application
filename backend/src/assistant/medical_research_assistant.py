# src/assistant/medical_research_assistant.py

import os
from typing import Dict
from langchain_google_genai import GoogleGenerativeAI
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
from datetime import datetime
from dotenv import load_dotenv

# Import data fetchers
from ..data_fetchers.pubmed_fetcher import PubMedFetcher
from ..data_fetchers.clinicaltrials_fetcher import ClinicalTrialsFetcher
from ..data_fetchers.medrxiv_fetcher import MedRxivFetcher
from ..data_fetchers.cdc_fetcher import CDCFetcher
from ..data_fetchers.nih_fetcher import NIHFetcher
from ..utils.database_handler import MedicalResearchDB

class MedicalResearchAssistant:
    def __init__(self, gemini_api_key: str = None, pubmed_api_key: str = None):
        """Initialize the Medical Research Assistant"""
        load_dotenv()

        self.gemini_api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        self.pubmed_api_key = pubmed_api_key or os.getenv('PUBMED_API_KEY')

        if not self.gemini_api_key:
            raise ValueError("Gemini API key is required")

        # Initialize LLM
        self.llm = GoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.gemini_api_key,
            temperature=0.3
        )

        # Initialize data fetchers
        self.pubmed_fetcher = PubMedFetcher(self.pubmed_api_key)
        self.trials_fetcher = ClinicalTrialsFetcher()
        self.medrxiv_fetcher = MedRxivFetcher()
        self.cdc_fetcher = CDCFetcher()
        self.nih_fetcher = NIHFetcher()

        # Initialize database connection
        self.db = MedicalResearchDB()

        # Setup tools
        self._setup_tools()

    def _setup_tools(self):
        """Setup tools for the LangChain agent"""
        self.tools = {
            "pubmed": Tool(
                name="analyze_pubmed",
                func=self.analyze_pubmed_content,
                description="Extracts insights from PubMed research articles"
            ),
            "clinical_trials": Tool(
                name="analyze_trials",
                func=self.analyze_trial_content,
                description="Analyzes clinical trials related to rare diseases"
            ),
            "research_papers": Tool(
                name="analyze_papers",
                func=self.analyze_paper_content,
                description="Summarizes findings from MedRxiv/BioRxiv research papers"
            ),
            "cdc_data": Tool(
                name="analyze_cdc_data",
                func=self.analyze_disease_content,
                description="Analyzes CDC surveillance data for disease trends"
            ),
            "nih": Tool(
                name="analyze_nih",
                func=self.analyze_nih_content,
                description="Summarizes NIH-funded projects relevant to the query"
            )
        }

    def analyze_pubmed_content(self, query: str) -> str:
        """Analyze PubMed content using LLM"""
        print("Fetching data from PubMed...")
        content = self.pubmed_fetcher.fetch_and_summarize(query)
        if not content:
            return None
        prompt = PromptTemplate(
            template="Summarize recent PubMed research on {query}:\n\n{content}",
            input_variables=["query", "content"]
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.invoke({"query": query, "content": content})["text"]

    def analyze_trial_content(self, query: str) -> str:
        """Analyze clinical trial content using LLM"""
        print("Fetching clinical trial data...")
        content = self.trials_fetcher.fetch_and_summarize_trials(query)
        if not content:
            return None
        prompt = PromptTemplate(
            template="Analyze these clinical trials related to {query}:\n\n{content}",
            input_variables=["query", "content"]
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.invoke({"query": query, "content": content})["text"]

    def analyze_paper_content(self, query: str) -> str:
        """Analyze research paper content using LLM"""
        print("Fetching research papers...")
        content = self.medrxiv_fetcher.fetch_and_summarize_rare_disease_papers()
        if not content:
            return None
        prompt = PromptTemplate(
            template="Analyze these research papers related to {query}:\n\n{content}",
            input_variables=["query", "content"]
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.invoke({"query": query, "content": content})["text"]

    def analyze_disease_content(self, query: str) -> str:
        """Analyze CDC disease content using LLM"""
        print("Fetching CDC data...")
        content = self.cdc_fetcher.fetch_and_summarize_rare_diseases()
        if not content:
            return None
        prompt = PromptTemplate(
            template="Analyze this CDC disease data related to {query}:\n\n{content}",
            input_variables=["query", "content"]
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.invoke({"query": query, "content": content})["text"]

    def analyze_nih_content(self, query: str) -> str:
        """Analyze NIH project content using LLM"""
        print("Fetching NIH data...")
        content = self.nih_fetcher.fetch_and_summarize_nih_projects(query)
        if not content:
            return None
        prompt = PromptTemplate(
            template="Analyze these NIH research projects related to {query}:\n\n{content}",
            input_variables=["query", "content"]
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain.invoke({"query": query, "content": content})["text"]

    def summarize_response(self, raw_response: str, query: str) -> str:
        """Process raw response through LLM for a concise summary"""
        summary_prompt = PromptTemplate(
            template="""Please analyze and synthesize the following medical research information into a clear, concise response.
            Focus on the most relevant and important points related to the query.

            Query: {query}

            Raw Information:
            {raw_response}

            Please provide a well-structured response that:
            1. Prioritizes the most relevant findings
            2. Highlights key clinical or research developments
            3. Removes redundant information
            4. Maintains scientific accuracy
            5. Is easy to understand

            Response should include:
            - Key findings or developments
            - Important research outcomes
            - Clinical implications (if applicable)
            - Relevant statistics or data points
            """,
            input_variables=["query", "raw_response"]
        )

        chain = LLMChain(llm=self.llm, prompt=summary_prompt)
        summary = chain.invoke({
            "query": query,
            "raw_response": raw_response
        })["text"]

        return summary

    def fetch_analysis(self, analysis_type: str) -> str:
        """Fetch analysis for trends, clinical, or general research"""
        query = ""
        if analysis_type == "recent_trends":
            query = "current trends in rare disease research"
        elif analysis_type == "clinical":
            query = "latest clinical trials and treatments for rare diseases"
        elif analysis_type == "research":
            query = "current medical research on rare diseases"

        print(f"\nFetching {analysis_type} analysis...")
        analysis_results = {}

        for tool_name, tool in self.tools.items():
            try:
                result = tool.func(query)
                if result:
                    analysis_results[tool_name] = result
            except Exception as e:
                print(f"Error with {tool_name}: {e}")
                continue

        if not analysis_results:
            return None

        raw_response = self._format_overview(f"{analysis_type.capitalize()} Analysis",
                                         analysis_results)
        return self.summarize_response(raw_response, query)

    def answer_specific_query(self, query: str) -> str:
        """Answer specific user query with enhanced processing"""
        try:
            self.db.connect()

            print("\nGathering information from multiple sources...")
            analysis_results = {}

            for tool_name, tool in self.tools.items():
                try:
                    result = tool.func(query)
                    if result:
                        analysis_results[tool_name] = result
                except Exception as e:
                    print(f"Error with {tool_name}: {e}")
                    continue

            if not analysis_results:
                return "I couldn't find enough relevant information to answer your query."

            raw_response = self._format_overview("Analysis Results", analysis_results)
            final_response = self.summarize_response(raw_response, query)

            self.db.store_query_result(
                query=query,
                response=final_response,
                metadata={
                    "timestamp": datetime.now(),
                    "query_type": "specific",
                    "sources_used": list(self.tools.keys())
                }
            )

            return final_response

        finally:
            self.db.close()

    def _format_overview(self, title: str, analysis: dict) -> str:
        """Format analysis results for LLM processing"""
        sections = []
        for source, content in analysis.items():
            sections.append(f"=== {source.upper()} ===")
            sections.append(content)

        return "\n\n".join(sections)