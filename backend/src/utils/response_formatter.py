
from typing import List
import textwrap

class ResponseFormatter:
    @staticmethod
    def format_sections(text: str) -> str:
        """Format response into clear sections with proper spacing"""
        lines = text.split('\n')
        formatted_lines = []
        current_section = []

        for line in lines:
            if line.startswith('•') or line.startswith('-'):
                if current_section:
                    formatted_lines.extend(current_section)
                    formatted_lines.append('')
                current_section = [line]
            elif line.strip() == '':
                if current_section:
                    formatted_lines.extend(current_section)
                    formatted_lines.append('')
                current_section = []
            else:
                wrapped = textwrap.fill(line, width=80)
                current_section.extend(wrapped.split('\n'))

        if current_section:
            formatted_lines.extend(current_section)

        return '\n'.join(formatted_lines)

    @staticmethod
    def add_summary_header(query: str, text: str) -> str:
        """Add a header with the query and formatting"""
        header = [
            "=" * 80,
            f"Query: {query}",
            "=" * 80,
            "",
            text
        ]
        return '\n'.join(header)

    @staticmethod
    def format_key_findings(findings: List[str]) -> str:
        """Format key findings with bullets and proper spacing"""
        formatted = ["Key Findings:", ""]
        for finding in findings:
            formatted.append(f"• {finding}")
        return '\n'.join(formatted)