from typing import Dict, List
import textwrap
from datetime import datetime

class DataFormatter:
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency with appropriate suffix for large numbers"""
        if amount >= 1_000_000:
            return f"${amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.1f}K"
        else:
            return f"${amount:.2f}"

    @staticmethod
    def wrap_text(text: str, width: int = 80, indent: str = "") -> str:
        """Wrap text to specified width with optional indentation"""
        if not text:
            return ""
        return textwrap.fill(text, width=width, initial_indent=indent,
                           subsequent_indent=indent)

    @staticmethod
    def format_date(date_str: str, input_format: str = "%Y-%m-%d",
                   output_format: str = "%B %d, %Y") -> str:
        """Format date string to desired format"""
        try:
            date_obj = datetime.strptime(date_str, input_format)
            return date_obj.strftime(output_format)
        except (ValueError, TypeError):
            return date_str

    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Format float as percentage string"""
        return f"{value:.{decimal_places}f}%"

    @staticmethod
    def format_list_items(items: List[str], separator: str = ", ") -> str:
        """Format list of items into a string with specified separator"""
        if not items:
            return "N/A"
        return separator.join(items)

    @staticmethod
    def create_section_header(title: str, char: str = "=") -> str:
        """Create a section header with title and underline"""
        return f"\n{title}\n{char * len(title)}"

    @staticmethod
    def format_key_value(key: str, value: str, separator: str = ": ") -> str:
        """Format key-value pair with specified separator"""
        return f"{key}{separator}{value}"

    @staticmethod
    def create_table_row(columns: List[str], widths: List[int]) -> str:
        """Create a formatted table row with specified column widths"""
        row = []
        for text, width in zip(columns, widths):
            row.append(str(text).ljust(width))
        return " | ".join(row)

    @staticmethod
    def create_progress_bar(value: float, total: float, width: int = 50) -> str:
        """Create a text-based progress bar"""
        percentage = value / total
        filled = int(width * percentage)
        bar = "█" * filled + "-" * (width - filled)
        return f"[{bar}] {percentage:.1%}"