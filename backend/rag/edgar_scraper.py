"""
SEC EDGAR scraper for downloading and parsing 10-K and 10-Q filings.
Complies with SEC.gov access rules and rate limits.
"""
from sec_edgar_downloader import Downloader
from typing import Optional, List, Dict
import os
import re
from pathlib import Path
import logging
from bs4 import BeautifulSoup

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class EDGARScraper:
    """Scraper for SEC EDGAR filings."""

    def __init__(self):
        """Initialize EDGAR downloader with user agent."""
        self.download_folder = Path("./data/edgar_filings")
        self.download_folder.mkdir(parents=True, exist_ok=True)

        self.downloader = Downloader(
            company_name="InvestmentResearch",
            email_address=settings.sec_edgar_user_agent.split()[-1],  # Extract email
            download_folder=str(self.download_folder)
        )

    def download_filing(
        self,
        ticker: str,
        filing_type: str = "10-K",
        num_filings: int = 1,
        after_date: Optional[str] = None,
        before_date: Optional[str] = None
    ) -> List[Path]:
        """
        Download SEC filings for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            filing_type: Type of filing ("10-K", "10-Q", "8-K", etc.)
            num_filings: Number of recent filings to download
            after_date: Download filings after this date (YYYYMMDD)
            before_date: Download filings before this date (YYYYMMDD)

        Returns:
            List of paths to downloaded filing files
        """
        try:
            logger.info(f"Downloading {num_filings} {filing_type} filing(s) for {ticker}")

            # Download filings
            self.downloader.get(
                filing_type,
                ticker,
                limit=num_filings,
                after=after_date,
                before=before_date,
                download_details=True
            )

            # Find downloaded files
            filing_dir = self.download_folder / "sec-edgar-filings" / ticker / filing_type
            filing_paths = []

            if filing_dir.exists():
                # Get all filing folders sorted by date (most recent first)
                filing_folders = sorted(
                    [f for f in filing_dir.iterdir() if f.is_dir()],
                    reverse=True
                )[:num_filings]

                for folder in filing_folders:
                    # Look for the main filing document
                    filing_file = folder / "full-submission.txt"
                    if filing_file.exists():
                        filing_paths.append(filing_file)

            logger.info(f"✅ Downloaded {len(filing_paths)} {filing_type} filing(s) for {ticker}")
            return filing_paths

        except Exception as e:
            logger.error(f"❌ Failed to download {filing_type} for {ticker}: {e}")
            return []

    def parse_filing(self, filing_path: Path) -> Dict[str, str]:
        """
        Parse a downloaded filing to extract text content.

        Args:
            filing_path: Path to the filing file

        Returns:
            Dict with filing metadata and content
        """
        try:
            with open(filing_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract HTML content (filings are usually in HTML/SGML format)
            soup = BeautifulSoup(content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Extract metadata from filename/path
            # Path structure: .../sec-edgar-filings/TICKER/FILING_TYPE/ACCESSION/file
            parts = filing_path.parts
            ticker = parts[-4] if len(parts) >= 4 else "UNKNOWN"
            filing_type = parts[-3] if len(parts) >= 3 else "UNKNOWN"
            filing_date = parts[-2] if len(parts) >= 2 else "UNKNOWN"  # Accession number

            return {
                "ticker": ticker.upper(),
                "filing_type": filing_type,
                "filing_date": filing_date,
                "file_path": str(filing_path),
                "content": text
            }

        except Exception as e:
            logger.error(f"❌ Failed to parse filing {filing_path}: {e}")
            return {}

    def extract_sections(self, filing_content: str) -> Dict[str, str]:
        """
        Extract key sections from a 10-K or 10-Q filing.

        Common sections in 10-K:
        - Item 1: Business
        - Item 1A: Risk Factors
        - Item 7: Management's Discussion and Analysis (MD&A)
        - Item 8: Financial Statements

        Args:
            filing_content: Full text content of the filing

        Returns:
            Dict mapping section names to their content
        """
        sections = {}

        # Patterns for common 10-K/10-Q sections
        section_patterns = {
            "Business": r"ITEM\s+1\.?\s+BUSINESS",
            "Risk Factors": r"ITEM\s+1A\.?\s+RISK FACTORS",
            "MD&A": r"ITEM\s+7\.?\s+MANAGEMENT'?S DISCUSSION AND ANALYSIS",
            "Financial Statements": r"ITEM\s+8\.?\s+FINANCIAL STATEMENTS",
            "Properties": r"ITEM\s+2\.?\s+PROPERTIES",
            "Legal Proceedings": r"ITEM\s+3\.?\s+LEGAL PROCEEDINGS"
        }

        try:
            for section_name, pattern in section_patterns.items():
                # Find section start
                match = re.search(pattern, filing_content, re.IGNORECASE)
                if match:
                    start = match.end()

                    # Find next section (approximately)
                    # Look for next "ITEM" marker
                    next_section = re.search(r"ITEM\s+\d+[A-Z]?\.?", filing_content[start:], re.IGNORECASE)

                    if next_section:
                        end = start + next_section.start()
                    else:
                        # If no next section found, take next 10000 characters
                        end = start + 10000

                    section_text = filing_content[start:end].strip()

                    # Clean up section text
                    section_text = re.sub(r'\s+', ' ', section_text)

                    if len(section_text) > 100:  # Only keep substantial sections
                        sections[section_name] = section_text

            if sections:
                logger.info(f"✅ Extracted {len(sections)} sections from filing")
            else:
                logger.warning("⚠️  No sections extracted, using full content")
                sections["Full Content"] = filing_content[:50000]  # First 50K chars

        except Exception as e:
            logger.error(f"❌ Failed to extract sections: {e}")
            sections["Full Content"] = filing_content[:50000]

        return sections

    def get_filing_summary(
        self,
        ticker: str,
        filing_type: str = "10-K",
        num_filings: int = 1
    ) -> List[Dict]:
        """
        Download and parse filings, returning structured summaries.

        Args:
            ticker: Stock ticker
            filing_type: Type of filing
            num_filings: Number of filings to process

        Returns:
            List of dicts with parsed filing data
        """
        summaries = []

        # Download filings
        filing_paths = self.download_filing(ticker, filing_type, num_filings)

        for filing_path in filing_paths:
            # Parse filing
            filing_data = self.parse_filing(filing_path)

            if filing_data:
                # Extract sections
                sections = self.extract_sections(filing_data["content"])
                filing_data["sections"] = sections

                # Remove full content to save memory
                del filing_data["content"]

                summaries.append(filing_data)

        return summaries


# Singleton instance
edgar_scraper = EDGARScraper()
