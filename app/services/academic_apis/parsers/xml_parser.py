"""
XML response parser for academic APIs.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional


class XMLParser:
    """
    Unified XML parser for academic APIs that return XML responses.
    """

    @staticmethod
    def parse_pubmed_article(article_xml: ET.Element) -> Dict[str, Any]:
        """
        Parse PubMed article XML to dictionary.

        Args:
            article_xml: XML element representing a PubMed article

        Returns:
            Dictionary with paper data
        """
        paper = {}

        # Extract PMID
        pmid_elem = article_xml.find(".//PMID")
        if pmid_elem is not None:
            paper["pmid"] = pmid_elem.text

        # Extract PMC ID
        pmc_elem = article_xml.find(".//ArticleId[@IdType='pmc']")
        if pmc_elem is not None:
            pmcid = pmc_elem.text
            paper["pmcid"] = pmcid
        else:
            pmcid = None
        
        # Extract DOI
        doi_elem = article_xml.find(".//ArticleId[@IdType='doi']")
        if doi_elem is not None:
            paper["doi"] = doi_elem.text

        # Extract title
        title_elem = article_xml.find(".//ArticleTitle")
        if title_elem is not None:
            paper["title"] = XMLParser._get_text_content(title_elem)

        # Extract abstract
        abstract_elem = article_xml.find(".//Abstract/AbstractText")
        if abstract_elem is not None:
            paper["abstract"] = XMLParser._get_text_content(abstract_elem)

        # Extract authors
        paper["authors"] = XMLParser._extract_pubmed_authors(article_xml)

        # Extract journal information
        journal_info = XMLParser._extract_pubmed_journal_info(article_xml)
        paper.update(journal_info)

        # Extract publication date
        pub_date = XMLParser._extract_pubmed_date(article_xml)
        if pub_date:
            paper["publicationDate"] = pub_date

        # Extract MeSH terms
        paper["meshTerms"] = XMLParser._extract_mesh_terms(article_xml)

        # Extract keywords
        paper["keywords"] = XMLParser._extract_keywords(article_xml)
        
        # Build URLs
        if pmid_elem is not None and pmid_elem.text:
            paper["paperUrl"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid_elem.text}/"
        if pmcid:
            paper["pdfUrl"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf"
        
        return paper

    @staticmethod
    def _get_text_content(element: ET.Element) -> str:
        """Get text content from XML element, including nested elements."""
        if element.text:
            text_parts = [element.text]
        else:
            text_parts = []

        for child in element:
            if child.text:
                text_parts.append(child.text)
            if child.tail:
                text_parts.append(child.tail)

        return "".join(text_parts).strip()

    @staticmethod
    def _extract_pubmed_authors(article_xml: ET.Element) -> List[Dict[str, Any]]:
        """Extract author information from PubMed XML."""
        authors = []

        for author_elem in article_xml.findall(".//Author"):
            author = {}

            # Extract name components
            last_name = author_elem.find("LastName")
            first_name = author_elem.find("ForeName")
            initials = author_elem.find("Initials")

            if last_name is not None and first_name is not None:
                author["name"] = f"{first_name.text} {last_name.text}"
            elif last_name is not None and initials is not None:
                author["name"] = f"{initials.text} {last_name.text}"
            elif last_name is not None:
                author["name"] = last_name.text
            else:
                continue

            # Extract affiliation
            affiliation_elem = author_elem.find("AffiliationInfo/Affiliation")
            if affiliation_elem is not None:
                author["affiliation"] = affiliation_elem.text

            # Extract ORCID if available
            identifier_elem = author_elem.find("Identifier[@Source='ORCID']")
            if identifier_elem is not None:
                author["orcid"] = identifier_elem.text

            author["authorId"] = None
            author["gsProfileUrl"] = None

            authors.append(author)

        return authors

    @staticmethod
    def _extract_pubmed_journal_info(article_xml: ET.Element) -> Dict[str, Any]:
        """Extract journal information from PubMed XML."""
        journal_info = {}

        # Journal name
        journal_elem = article_xml.find(".//Journal/Title") or article_xml.find(
            ".//Journal/ISOAbbreviation"
        )
        if journal_elem is not None:
            journal_info["venueName"] = journal_elem.text

        # ISSN
        issn_elem = article_xml.find(".//Journal/ISSN")
        if issn_elem is not None:
            journal_info["issn"] = issn_elem.text

        # Volume and Issue
        volume_elem = article_xml.find(".//JournalIssue/Volume")
        if volume_elem is not None:
            journal_info["volume"] = volume_elem.text

        issue_elem = article_xml.find(".//JournalIssue/Issue")
        if issue_elem is not None:
            journal_info["issue"] = issue_elem.text

        # Pages
        pagination_elem = article_xml.find(".//Pagination/MedlinePgn")
        if pagination_elem is not None:
            journal_info["pages"] = pagination_elem.text

        return journal_info

    @staticmethod
    def _extract_pubmed_date(article_xml: ET.Element) -> Optional[str]:
        """Extract publication date from PubMed XML."""
        # Try different date elements
        date_elems = [
            article_xml.find(".//PubDate"),
            article_xml.find(".//ArticleDate[@DateType='Electronic']"),
            article_xml.find(".//DateCompleted"),
        ]

        for date_elem in date_elems:
            if date_elem is not None:
                year = date_elem.find("Year")
                month = date_elem.find("Month")
                day = date_elem.find("Day")

                if year is not None:
                    year_val = year.text
                    month_val = month.text if month is not None else "01"
                    day_val = day.text if day is not None else "01"

                    # Convert month name to number if needed
                    month_map = {
                        "Jan": "01",
                        "Feb": "02",
                        "Mar": "03",
                        "Apr": "04",
                        "May": "05",
                        "Jun": "06",
                        "Jul": "07",
                        "Aug": "08",
                        "Sep": "09",
                        "Oct": "10",
                        "Nov": "11",
                        "Dec": "12",
                    }

                    if month_val in month_map:
                        month_val = month_map[month_val]

                    try:
                        # Ensure proper formatting
                        month_val = f"{int(month_val.strip()):02d}"
                        day_val = f"{int(day_val.strip()):02d}"
                        return f"{year_val}-{month_val}-{day_val}"
                    except (ValueError, AttributeError):
                        return f"{year_val}-01-01"

        return None

    @staticmethod
    def _extract_mesh_terms(article_xml: ET.Element) -> List[str]:
        """Extract MeSH terms from PubMed XML."""
        mesh_terms = []

        for mesh_elem in article_xml.findall(".//MeshHeading/DescriptorName"):
            if mesh_elem.text:
                mesh_terms.append(mesh_elem.text)

        return mesh_terms

    @staticmethod
    def _extract_keywords(article_xml: ET.Element) -> List[str]:
        """Extract keywords from PubMed XML."""
        keywords = []

        for keyword_elem in article_xml.findall(".//Keyword"):
            if keyword_elem.text:
                keywords.append(keyword_elem.text)

        return keywords

    @staticmethod
    def parse_dblp_paper(paper_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse DBLP paper info (from JSON API) to standardized format.

        Args:
            paper_info: DBLP paper info dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields
        if "title" in paper_info:
            result["title"] = paper_info["title"]

        # Extract authors
        if "authors" in paper_info:
            result["authors"] = XMLParser._extract_dblp_authors(paper_info["authors"])

        # Extract venue
        if "venue" in paper_info:
            result["venueName"] = paper_info["venue"]

        # Extract publication year
        if "year" in paper_info:
            result["publicationDate"] = f"{paper_info['year']}-01-01"

        # Extract type
        if "type" in paper_info:
            result["type"] = paper_info["type"]

        # Extract pages
        if "pages" in paper_info:
            result["pages"] = paper_info["pages"]

        # Extract volume/number
        if "volume" in paper_info:
            result["volume"] = paper_info["volume"]
        if "number" in paper_info:
            result["issue"] = paper_info["number"]

        # Extract DOI if available
        if "doi" in paper_info:
            result["doi"] = paper_info["doi"]

        # Extract DBLP key/URL
        if "key" in paper_info:
            result["dblpKey"] = paper_info["key"]
        if "url" in paper_info:
            result["paperUrl"] = paper_info["url"]

        # Extract publisher
        if "publisher" in paper_info:
            result["publisher"] = paper_info["publisher"]

        # Extract ISBN
        if "isbn" in paper_info:
            result["isbn"] = paper_info["isbn"]

        return result

    @staticmethod
    def _extract_dblp_authors(authors_data) -> List[Dict[str, Any]]:
        """Extract author information from DBLP data."""
        authors = []

        if isinstance(authors_data, dict) and "author" in authors_data:
            author_list = authors_data["author"]
            if isinstance(author_list, list):
                for author in author_list:
                    if isinstance(author, dict):
                        author_info = {
                            "name": author.get("text", author.get("@pid", "")),
                            "authorId": author.get("@pid"),
                            "orcid": author.get("@orcid"),
                            "affiliation": None,
                            "gsProfileUrl": None,
                        }
                    elif isinstance(author, str):
                        author_info = {
                            "name": author,
                            "authorId": None,
                            "orcid": None,
                            "affiliation": None,
                            "gsProfileUrl": None,
                        }
                    else:
                        continue

                    if author_info["name"]:
                        authors.append(author_info)
            elif isinstance(author_list, str):
                authors.append(
                    {
                        "name": author_list,
                        "authorId": None,
                        "orcid": None,
                        "affiliation": None,
                        "gsProfileUrl": None,
                    }
                )
        elif isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, str):
                    authors.append(
                        {
                            "name": author,
                            "authorId": None,
                            "orcid": None,
                            "affiliation": None,
                            "gsProfileUrl": None,
                        }
                    )
        elif isinstance(authors_data, str):
            authors.append(
                {
                    "name": authors_data,
                    "authorId": None,
                    "orcid": None,
                    "affiliation": None,
                    "gsProfileUrl": None,
                }
            )

        return authors

    @staticmethod
    def parse_dblp_xml_element(element: ET.Element) -> Dict[str, Any]:
        """
        Parse DBLP XML element to dictionary format.

        Args:
            element: XML element representing a DBLP publication

        Returns:
            Dictionary with publication data
        """
        result = {}

        # Extract title
        title_elem = element.find("title")
        if title_elem is not None:
            result["title"] = title_elem.text

        # Extract authors
        authors = []
        for author_elem in element.findall("author"):
            if author_elem.text:
                author_info = {
                    "name": author_elem.text,
                    "authorId": author_elem.get("pid"),
                    "orcid": author_elem.get("orcid"),
                    "affiliation": None,
                    "gsProfileUrl": None,
                }
                authors.append(author_info)
        result["authors"] = authors

        # Extract venue based on publication type
        if element.tag == "article":
            journal_elem = element.find("journal")
            if journal_elem is not None:
                result["venueName"] = journal_elem.text
        elif element.tag == "inproceedings":
            booktitle_elem = element.find("booktitle")
            if booktitle_elem is not None:
                result["venueName"] = booktitle_elem.text

        # Extract year
        year_elem = element.find("year")
        if year_elem is not None:
            result["publicationDate"] = f"{year_elem.text}-01-01"

        # Extract volume/number
        volume_elem = element.find("volume")
        if volume_elem is not None:
            result["volume"] = volume_elem.text

        number_elem = element.find("number")
        if number_elem is not None:
            result["issue"] = number_elem.text

        # Extract pages
        pages_elem = element.find("pages")
        if pages_elem is not None:
            result["pages"] = pages_elem.text

        # Extract DOI
        doi_elem = element.find("doi")
        if doi_elem is not None:
            result["doi"] = doi_elem.text

        # Extract URL
        url_elem = element.find("url")
        if url_elem is not None:
            result["paperUrl"] = url_elem.text

        # Extract publisher
        publisher_elem = element.find("publisher")
        if publisher_elem is not None:
            result["publisher"] = publisher_elem.text

        # Extract ISBN
        isbn_elem = element.find("isbn")
        if isbn_elem is not None:
            result["isbn"] = isbn_elem.text

        # Set publication type
        result["type"] = element.tag

        # Extract DBLP key
        if "key" in element.attrib:
            result["dblpKey"] = element.attrib["key"]

        return result
