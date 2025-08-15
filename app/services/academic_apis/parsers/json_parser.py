"""
JSON response parser for academic APIs.
"""

from typing import Dict, Any, List, Optional


class JSONParser:
    """
    Unified JSON parser for academic APIs that return JSON responses.
    """

    @staticmethod
    def parse_crossref_work(work: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Crossref work data to standardized format.

        Args:
            work: Crossref work dictionary

        Returns:
            Standardized paper dictionary
        """
        paper = {}

        # Extract DOI
        if "DOI" in work:
            paper["doi"] = work["DOI"]

        # Extract title (Crossref titles are arrays)
        if "title" in work and work["title"]:
            paper["title"] = (
                work["title"][0] if isinstance(work["title"], list) else work["title"]
            )

        # Extract authors
        paper["authors"] = JSONParser._extract_crossref_authors(work)

        # Extract container title (journal/venue)
        if "container-title" in work and work["container-title"]:
            container = work["container-title"]
            paper["venueName"] = (
                container[0] if isinstance(container, list) else container
            )

        # Extract publisher
        if "publisher" in work:
            paper["publisher"] = work["publisher"]

        # Extract publication date
        paper["publicationDate"] = JSONParser._extract_crossref_date(work)

        # Extract type
        if "type" in work:
            paper["type"] = work["type"]

        # Extract ISSN/ISBN
        if "ISSN" in work:
            paper["ISSN"] = work["ISSN"]
        if "ISBN" in work:
            paper["ISBN"] = work["ISBN"]

        # Extract abstract if available
        if "abstract" in work:
            paper["abstract"] = work["abstract"]

        # Extract page info
        if "page" in work:
            paper["pages"] = work["page"]

        # Extract volume/issue
        if "volume" in work:
            paper["volume"] = work["volume"]
        if "issue" in work:
            paper["issue"] = work["issue"]

        # Extract license info
        if "license" in work:
            paper["license"] = work["license"]

        # Extract funder info
        if "funder" in work:
            paper["funder"] = work["funder"]

        # Extract URL
        if "URL" in work:
            paper["paperUrl"] = work["URL"]

        return paper

    @staticmethod
    def _extract_crossref_authors(work: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract author information from Crossref work."""
        authors = []

        if "author" in work and isinstance(work["author"], list):
            for author in work["author"]:
                author_info = {
                    "name": "",
                    "orcid": None,
                    "affiliation": None,
                    "authorId": None,
                    "gsProfileUrl": None,
                }

                # Build name from given/family components
                given = author.get("given", "")
                family = author.get("family", "")

                if given and family:
                    author_info["name"] = f"{given} {family}"
                elif family:
                    author_info["name"] = family
                elif given:
                    author_info["name"] = given

                # Extract ORCID
                if "ORCID" in author:
                    author_info["orcid"] = author["ORCID"].replace(
                        "http://orcid.org/", ""
                    )

                # Extract affiliation
                if "affiliation" in author and author["affiliation"]:
                    affiliations = author["affiliation"]
                    if isinstance(affiliations, list) and affiliations:
                        # Take first affiliation name
                        first_aff = affiliations[0]
                        if isinstance(first_aff, dict) and "name" in first_aff:
                            author_info["affiliation"] = first_aff["name"]
                        elif isinstance(first_aff, str):
                            author_info["affiliation"] = first_aff

                if author_info["name"]:
                    authors.append(author_info)

        return authors

    @staticmethod
    def _extract_crossref_date(work: Dict[str, Any]) -> Optional[str]:
        """Extract publication date from Crossref work."""
        # Try different date fields
        date_fields = ["published-print", "published-online", "created", "deposited"]

        for field in date_fields:
            if field in work and "date-parts" in work[field]:
                date_parts = work[field]["date-parts"]
                if date_parts and isinstance(date_parts[0], list):
                    parts = date_parts[0]
                    if len(parts) >= 1:
                        year = parts[0]
                        month = parts[1] if len(parts) > 1 else 1
                        day = parts[2] if len(parts) > 2 else 1

                        try:
                            return f"{year:04d}-{month:02d}-{day:02d}"
                        except (ValueError, TypeError):
                            return f"{year}-01-01"

        return None

    @staticmethod
    def parse_semantic_scholar_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Semantic Scholar paper data.

        Args:
            paper: Semantic Scholar paper dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields
        if "title" in paper:
            result["title"] = paper["title"]

        if "abstract" in paper:
            result["abstract"] = paper["abstract"]

        # Extract paper ID
        if "paperId" in paper:
            result["semanticScholarId"] = paper["paperId"]

        # Extract external IDs
        if "externalIds" in paper:
            result["externalIds"] = paper["externalIds"]
            # Extract DOI from external IDs
            if "DOI" in paper["externalIds"]:
                result["doi"] = paper["externalIds"]["DOI"]

        # Extract authors
        if "authors" in paper:
            result["authors"] = JSONParser._extract_semantic_scholar_authors(
                paper["authors"]
            )

        # Extract venue
        if "venue" in paper:
            result["venueName"] = paper["venue"]

        # Extract journal info
        if "journal" in paper and paper["journal"]:
            journal = paper["journal"]
            if not result.get("venueName") and "name" in journal:
                result["venueName"] = journal["name"]
            if "publisher" in journal:
                result["publisher"] = journal["publisher"]

        # Extract metrics
        if "citationCount" in paper:
            result["citationCount"] = paper["citationCount"]
        if "referenceCount" in paper:
            result["referenceCount"] = paper["referenceCount"]
        if "influentialCitationCount" in paper:
            result["influentialCitationCount"] = paper["influentialCitationCount"]

        # Extract dates
        if "publicationDate" in paper:
            result["publicationDate"] = paper["publicationDate"]
        elif "year" in paper:
            result["publicationDate"] = f"{paper['year']}-01-01"

        # Extract open access info
        if "isOpenAccess" in paper:
            result["isOpenAccess"] = paper["isOpenAccess"]

        if "openAccessPdf" in paper and paper["openAccessPdf"]:
            result["pdfUrl"] = paper["openAccessPdf"].get("url")

        # Extract additional fields
        if "publicationTypes" in paper:
            result["publicationTypes"] = paper["publicationTypes"]

        if "fieldsOfStudy" in paper:
            result["fieldsOfStudy"] = paper["fieldsOfStudy"]

        return result

    @staticmethod
    def _extract_semantic_scholar_authors(
        authors: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract author information from Semantic Scholar data."""
        result = []

        for author in authors:
            author_info = {
                "name": author.get("name", ""),
                "authorId": author.get("authorId"),
                "orcid": None,
                "gsProfileUrl": None,
                "affiliation": None,
            }

            # Extract ORCID from external IDs
            if "externalIds" in author and author["externalIds"]:
                if "ORCID" in author["externalIds"]:
                    author_info["orcid"] = author["externalIds"]["ORCID"]

            if author_info["name"]:
                result.append(author_info)

        return result

    @staticmethod
    def parse_openalex_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OpenAlex work data to standardized format.

        Args:
            paper: OpenAlex work dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields
        if "title" in paper:
            result["title"] = paper["title"]

        if "abstract" in paper:
            result["abstract"] = paper["abstract"]

        # Extract OpenAlex ID
        if "id" in paper:
            result["openAlexId"] = paper["id"]

        # Extract DOI
        if "doi" in paper and paper["doi"]:
            result["doi"] = paper["doi"].replace("https://doi.org/", "")

        # Extract authors from authorships
        if "authorships" in paper:
            result["authors"] = JSONParser._extract_openalex_authors(
                paper["authorships"]
            )

        # Extract venue/host venue
        if "host_venue" in paper and paper["host_venue"]:
            host_venue = paper["host_venue"]
            if "display_name" in host_venue:
                result["venueName"] = host_venue["display_name"]
            if "publisher" in host_venue:
                result["publisher"] = host_venue["publisher"]
            if "is_oa" in host_venue:
                result["isOpenAccess"] = host_venue["is_oa"]
            if "url" in host_venue:
                result["paperUrl"] = host_venue["url"]

        # Extract publication date
        if "publication_date" in paper:
            result["publicationDate"] = paper["publication_date"]
        elif "publication_year" in paper:
            result["publicationDate"] = f"{paper['publication_year']}-01-01"

        # Extract citation count
        if "cited_by_count" in paper:
            result["citationCount"] = paper["cited_by_count"]

        # Extract type
        if "type" in paper:
            result["type"] = paper["type"]

        # Extract concepts/topics
        if "concepts" in paper:
            result["concepts"] = [
                {"name": concept.get("display_name"), "score": concept.get("score")}
                for concept in paper["concepts"]
            ]

        # Extract open access information
        if "open_access" in paper:
            oa_info = paper["open_access"]
            result["isOpenAccess"] = oa_info.get("is_oa", False)
            result["oaStatus"] = oa_info.get("oa_status")

        # Extract referenced works
        if "referenced_works" in paper:
            result["referenced_works"] = paper["referenced_works"]

        return result

    @staticmethod
    def _extract_openalex_authors(
        authorships: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract author information from OpenAlex authorships."""
        authors = []

        for authorship in authorships:
            author_data = authorship.get("author", {})
            orcid = author_data.get("orcid")
            author_info = {
                "name": author_data.get("display_name", ""),
                "authorId": author_data.get("id"),
                "orcid": orcid.replace("https://orcid.org/", "") if orcid else None,
                "affiliation": None,
                "gsProfileUrl": None,
            }

            # Extract institutions
            institutions = authorship.get("institutions", [])
            if institutions:
                # Take first institution
                institution = institutions[0]
                author_info["affiliation"] = institution.get("display_name")

            if author_info["name"]:
                authors.append(author_info)

        return authors

    @staticmethod
    def parse_core_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse CORE paper data to standardized format.

        Args:
            paper: CORE work dictionary from API v3

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields
        if "title" in paper:
            result["title"] = paper["title"]

        if "abstract" in paper:
            result["abstract"] = paper["abstract"]
        elif "description" in paper:
            result["abstract"] = paper["description"]

        # Extract CORE ID
        if "id" in paper:
            result["coreId"] = str(paper["id"])

        # Extract DOI
        if "doi" in paper:
            result["doi"] = paper["doi"]
        elif "identifiers" in paper and isinstance(paper["identifiers"], dict):
            if "doi" in paper["identifiers"]:
                result["doi"] = paper["identifiers"]["doi"]

        # Extract authors
        if "authors" in paper:
            result["authors"] = JSONParser._extract_core_authors(paper["authors"])
        elif "contributors" in paper:
            result["authors"] = JSONParser._extract_core_authors(paper["contributors"])

        # Extract publication info
        if "publisher" in paper:
            result["publisher"] = paper["publisher"]

        # Extract journal/venue name
        if (
            "journals" in paper
            and isinstance(paper["journals"], list)
            and paper["journals"]
        ):
            result["venueName"] = paper["journals"][0].get("title", "")
        elif "journal" in paper:
            if isinstance(paper["journal"], dict):
                result["venueName"] = paper["journal"].get(
                    "title", paper["journal"].get("name", "")
                )
            else:
                result["venueName"] = str(paper["journal"])
        elif "source" in paper:
            result["venueName"] = paper["source"]

        # Extract dates - handle multiple possible date fields
        date_fields = [
            "publishedDate",
            "datePublished",
            "publicationDate",
            "yearPublished",
        ]
        for date_field in date_fields:
            if date_field in paper and paper[date_field]:
                if date_field == "yearPublished" and isinstance(
                    paper[date_field], (int, str)
                ):
                    result["publicationDate"] = f"{paper[date_field]}-01-01"
                else:
                    # Handle ISO date strings
                    date_str = str(paper[date_field])
                    if len(date_str) == 4 and date_str.isdigit():  # Just year
                        result["publicationDate"] = f"{date_str}-01-01"
                    else:
                        result["publicationDate"] = date_str.split("T")[
                            0
                        ]  # Remove time part if present
                break

        # Extract repository and download info
        if "repositories" in paper and isinstance(paper["repositories"], list):
            for repo in paper["repositories"]:
                if isinstance(repo, dict):
                    # Look for PDF URLs in repository data
                    if "openAccessUrl" in repo:
                        result["pdfUrl"] = repo["openAccessUrl"]
                        break
                    elif "downloadUrl" in repo:
                        result["pdfUrl"] = repo["downloadUrl"]
                        break
                    elif "fullTextUrl" in repo:
                        result["pdfUrl"] = repo["fullTextUrl"]
                        break

        # Extract direct download URL
        if not result.get("pdfUrl"):
            if "downloadUrl" in paper:
                result["pdfUrl"] = paper["downloadUrl"]
            elif "fullTextUrl" in paper:
                result["pdfUrl"] = paper["fullTextUrl"]
            elif "openAccessUrl" in paper:
                result["pdfUrl"] = paper["openAccessUrl"]

        # Extract language
        if "language" in paper:
            if isinstance(paper["language"], dict):
                result["language"] = paper["language"].get(
                    "name", paper["language"].get("code", "")
                )
            else:
                result["language"] = str(paper["language"])

        # Extract subject/topics
        if "topics" in paper and isinstance(paper["topics"], list):
            result["topics"] = [
                topic.get("name", str(topic)) if isinstance(topic, dict) else str(topic)
                for topic in paper["topics"]
            ]
        elif "subjects" in paper:
            result["topics"] = (
                paper["subjects"]
                if isinstance(paper["subjects"], list)
                else [paper["subjects"]]
            )

        # Mark as open access (CORE only indexes OA content)
        result["isOpenAccess"] = True

        # Extract additional metadata
        if "citationCount" in paper:
            result["citationCount"] = paper["citationCount"]

        if "magId" in paper:
            result["magId"] = str(paper["magId"])

        # Extract year separately if not found in date parsing
        if not result.get("publicationDate") and "year" in paper:
            result["publicationDate"] = f"{paper['year']}-01-01"

        return result

    @staticmethod
    def _extract_core_authors(authors_data) -> List[Dict[str, Any]]:
        """Extract author information from CORE data."""
        authors = []

        if isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, dict):
                    author_info = {
                        "name": "",
                        "authorId": None,
                        "orcid": None,
                        "affiliation": None,
                        "gsProfileUrl": None,
                    }

                    # Handle different name formats
                    if "name" in author:
                        author_info["name"] = author["name"]
                    elif "displayName" in author:
                        author_info["name"] = author["displayName"]
                    elif "fullName" in author:
                        author_info["name"] = author["fullName"]
                    else:
                        # Try to construct name from parts
                        name_parts = []
                        if "given" in author or "firstName" in author:
                            name_parts.append(
                                author.get("given", author.get("firstName", ""))
                            )
                        if "family" in author or "lastName" in author:
                            name_parts.append(
                                author.get("family", author.get("lastName", ""))
                            )
                        if name_parts:
                            author_info["name"] = " ".join(filter(None, name_parts))

                    # Extract author ID
                    if "id" in author:
                        author_info["authorId"] = str(author["id"])
                    elif "authorId" in author:
                        author_info["authorId"] = str(author["authorId"])

                    # Extract ORCID
                    if "orcid" in author:
                        orcid = author["orcid"]
                        if isinstance(orcid, str):
                            # Clean ORCID format
                            author_info["orcid"] = orcid.replace(
                                "https://orcid.org/", ""
                            ).replace("http://orcid.org/", "")

                    # Extract affiliation
                    if "affiliation" in author:
                        if isinstance(author["affiliation"], str):
                            author_info["affiliation"] = author["affiliation"]
                        elif isinstance(author["affiliation"], dict):
                            author_info["affiliation"] = author["affiliation"].get(
                                "name", ""
                            )
                        elif (
                            isinstance(author["affiliation"], list)
                            and author["affiliation"]
                        ):
                            first_aff = author["affiliation"][0]
                            if isinstance(first_aff, dict):
                                author_info["affiliation"] = first_aff.get("name", "")
                            else:
                                author_info["affiliation"] = str(first_aff)
                    elif (
                        "affiliations" in author
                        and isinstance(author["affiliations"], list)
                        and author["affiliations"]
                    ):
                        first_aff = author["affiliations"][0]
                        if isinstance(first_aff, dict):
                            author_info["affiliation"] = first_aff.get("name", "")
                        else:
                            author_info["affiliation"] = str(first_aff)

                    if author_info["name"]:
                        authors.append(author_info)
                elif isinstance(author, str):
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
            # Sometimes authors come as a string
            author_names = authors_data.split(", ")
            for name in author_names:
                if name.strip():
                    authors.append(
                        {
                            "name": name.strip(),
                            "authorId": None,
                            "orcid": None,
                            "affiliation": None,
                            "gsProfileUrl": None,
                        }
                    )

        return authors

    @staticmethod
    def parse_unpaywall_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Unpaywall paper data to standardized format.

        Args:
            paper: Unpaywall response dictionary

        Returns:
            Standardized paper dictionary
        """
        if not paper:
            return {}

        result = {}

        # Basic fields
        if "title" in paper and paper["title"]:
            result["title"] = paper["title"]

        # Extract DOI
        if "doi" in paper and paper["doi"]:
            result["doi"] = paper["doi"]

        # Extract URL
        if "doi_url" in paper and paper["doi_url"]:
            result["url"] = paper["doi_url"]

        # Extract publication info
        if "journal_name" in paper and paper["journal_name"]:
            result["venueName"] = paper["journal_name"]

        if "publisher" in paper and paper["publisher"]:
            result["publisher"] = paper["publisher"]

        # Extract publication year and dates
        if "year" in paper and paper["year"]:
            result["publicationDate"] = f"{paper['year']}-01-01"
            result["year"] = paper["year"]

        if "published_date" in paper and paper["published_date"]:
            result["publicationDate"] = paper["published_date"]

        # Extract open access information
        if "is_oa" in paper:
            result["isOpenAccess"] = bool(paper["is_oa"])

        # Extract OA locations with enhanced information
        if "oa_locations" in paper and paper["oa_locations"]:
            oa_locations = paper["oa_locations"]
            result["oa_locations"] = oa_locations

            # Extract best PDF URL (prefer repository over publisher)
            pdf_url = None
            landing_url = None

            # First pass: look for repository versions with PDFs
            for location in oa_locations:
                if location.get("host_type") == "repository" and location.get(
                    "url_for_pdf"
                ):
                    pdf_url = location["url_for_pdf"]
                    break

            # Second pass: any PDF URL
            if not pdf_url:
                for location in oa_locations:
                    if location.get("url_for_pdf"):
                        pdf_url = location["url_for_pdf"]
                        break

            # Extract landing page URL
            for location in oa_locations:
                if location.get("url"):
                    landing_url = location["url"]
                    break

            if pdf_url:
                result["pdfUrl"] = pdf_url
            if landing_url:
                result["landingPageUrl"] = landing_url

            # Extract OA type information
            oa_types = set()
            licenses = set()
            for location in oa_locations:
                if location.get("oa_version"):
                    oa_types.add(location["oa_version"])
                if location.get("license"):
                    licenses.add(location["license"])

            if oa_types:
                result["oa_types"] = list(oa_types)
            if licenses:
                result["licenses"] = list(licenses)

        # Extract metadata
        if "updated" in paper and paper["updated"]:
            result["lastUpdated"] = paper["updated"]

        # Extract additional identifiers
        if "pmid" in paper and paper["pmid"]:
            result["pmid"] = paper["pmid"]

        if "pmcid" in paper and paper["pmcid"]:
            result["pmcid"] = paper["pmcid"]

        # Extract bibliographic information
        if "journal_issns" in paper and paper["journal_issns"]:
            result["issn"] = paper["journal_issns"]

        if "journal_issn_l" in paper and paper["journal_issn_l"]:
            result["issnL"] = paper["journal_issn_l"]

        # Extract genre/type
        if "genre" in paper and paper["genre"]:
            result["publicationType"] = paper["genre"]

        # Extract z39.88 metadata if available
        if "z39_88" in paper and paper["z39_88"]:
            result["z39_88"] = paper["z39_88"]

        # Add source information
        result["source"] = "unpaywall"

        return result

    @staticmethod
    def parse_europepmc_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Europe PMC paper data to standardized format.

        Args:
            paper: Europe PMC result dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields
        if "title" in paper:
            result["title"] = paper["title"]

        if "abstractText" in paper:
            result["abstract"] = paper["abstractText"]

        # Extract IDs
        if "pmid" in paper:
            result["pmid"] = paper["pmid"]

        if "pmcid" in paper:
            result["pmcid"] = paper["pmcid"]

        if "doi" in paper:
            result["doi"] = paper["doi"]

        # Extract authors
        if "authorList" in paper and "author" in paper["authorList"]:
            result["authors"] = JSONParser._extract_europepmc_authors(
                paper["authorList"]["author"]
            )

        # Extract journal info
        if "journalInfo" in paper:
            journal_info = paper["journalInfo"]
            if "journal" in journal_info and "title" in journal_info["journal"]:
                result["venueName"] = journal_info["journal"]["title"]

            if "dateOfPublication" in journal_info:
                result["publicationDate"] = journal_info["dateOfPublication"]
            elif "yearOfPublication" in journal_info:
                result["publicationDate"] = f"{journal_info['yearOfPublication']}-01-01"

        # Extract publication type
        if "pubTypeList" in paper and "pubType" in paper["pubTypeList"]:
            pub_types = paper["pubTypeList"]["pubType"]
            if isinstance(pub_types, list) and pub_types:
                result["publicationType"] = pub_types[0]

        # Extract MeSH terms
        if "meshHeadingList" in paper and "meshHeading" in paper["meshHeadingList"]:
            mesh_terms = []
            for mesh in paper["meshHeadingList"]["meshHeading"]:
                if "descriptorName" in mesh:
                    mesh_terms.append(mesh["descriptorName"])
            result["meshTerms"] = mesh_terms

        # Extract full text availability
        if "hasTextMinedTerms" in paper:
            result["hasFullText"] = paper["hasTextMinedTerms"] == "Y"

        if "isOpenAccess" in paper:
            result["isOpenAccess"] = paper["isOpenAccess"] == "Y"

        # Extract source
        if "source" in paper:
            result["source"] = paper["source"]

        return result

    @staticmethod
    def _extract_europepmc_authors(
        authors_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract author information from Europe PMC data."""
        authors = []

        for author in authors_data:
            author_info = {
                "name": "",
                "authorId": None,
                "orcid": None,
                "affiliation": None,
                "gsProfileUrl": None,
            }

            # Build name
            first_name = author.get("firstName", "")
            last_name = author.get("lastName", "")
            initials = author.get("initials", "")

            if first_name and last_name:
                author_info["name"] = f"{first_name} {last_name}"
            elif last_name and initials:
                author_info["name"] = f"{initials} {last_name}"
            elif last_name:
                author_info["name"] = last_name

            # Extract affiliation
            if "affiliation" in author:
                author_info["affiliation"] = author["affiliation"]

            if author_info["name"]:
                authors.append(author_info)

        return authors

    @staticmethod
    def parse_biorxiv_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse bioRxiv/medRxiv paper data to standardized format.

        Args:
            paper: bioRxiv/medRxiv preprint dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields
        if "title" in paper:
            result["title"] = paper["title"]

        if "abstract" in paper:
            result["abstract"] = paper["abstract"]

        # Extract DOI
        if "doi" in paper:
            result["doi"] = paper["doi"]

        # Extract authors
        if "authors" in paper:
            result["authors"] = JSONParser._extract_biorxiv_authors(paper["authors"])

        # Extract dates
        if "date" in paper:
            result["publicationDate"] = paper["date"]

        # Extract category
        if "category" in paper:
            result["category"] = paper["category"]

        # Extract server info
        if "server" in paper:
            result["server"] = paper["server"]
            result["venueName"] = paper["server"]  # Use server as venue

        # Extract version
        if "version" in paper:
            result["version"] = paper["version"]

        # Mark as preprint
        result["type"] = "preprint"
        result["isPreprint"] = True

        # bioRxiv/medRxiv are open access
        result["isOpenAccess"] = True

        return result

    @staticmethod
    def _extract_biorxiv_authors(authors_data) -> List[Dict[str, Any]]:
        """Extract author information from bioRxiv/medRxiv data."""
        authors = []

        if isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, dict):
                    author_info = {
                        "name": author.get("name", ""),
                        "authorId": None,
                        "orcid": author.get("orcid"),
                        "affiliation": author.get("institution"),
                        "gsProfileUrl": None,
                    }

                    if author_info["name"]:
                        authors.append(author_info)
                elif isinstance(author, str):
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
            # Sometimes authors come as a string
            author_names = authors_data.split(", ")
            for name in author_names:
                authors.append(
                    {
                        "name": name.strip(),
                        "authorId": None,
                        "orcid": None,
                        "affiliation": None,
                        "gsProfileUrl": None,
                    }
                )

        return authors

    @staticmethod
    def parse_doaj_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse DOAJ article data to standardized format.

        Args:
            paper: DOAJ article dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}
        bibjson = paper.get("bibjson", {})

        # Basic fields
        if "title" in bibjson:
            result["title"] = bibjson["title"]

        if "abstract" in bibjson:
            result["abstract"] = bibjson["abstract"]

        # Extract identifiers
        if "identifier" in bibjson:
            for identifier in bibjson["identifier"]:
                if identifier.get("type") == "doi":
                    result["doi"] = identifier.get("id")
                elif identifier.get("type") == "pissn":
                    result["issn"] = identifier.get("id")
                elif identifier.get("type") == "eissn":
                    result["eissn"] = identifier.get("id")

        # Extract authors
        if "author" in bibjson:
            result["authors"] = JSONParser._extract_doaj_authors(bibjson["author"])

        # Extract journal info
        if "journal" in bibjson:
            journal = bibjson["journal"]
            if "title" in journal:
                result["venueName"] = journal["title"]
            if "publisher" in journal:
                result["publisher"] = journal["publisher"]
            if "country" in journal:
                result["country"] = journal["country"]

        # Extract date
        if "year" in bibjson:
            result["publicationDate"] = f"{bibjson['year']}-01-01"
        elif "month" in bibjson and "year" in bibjson:
            result["publicationDate"] = f"{bibjson['year']}-{bibjson['month']:02d}-01"

        # Extract subjects
        if "subject" in bibjson:
            subjects = []
            for subj in bibjson["subject"]:
                if "term" in subj:
                    subjects.append(subj["term"])
            result["subjects"] = subjects

        # Extract keywords
        if "keywords" in bibjson:
            result["keywords"] = bibjson["keywords"]

        # Extract language
        if "language" in bibjson:
            result["language"] = bibjson["language"]

        # DOAJ articles are always open access
        result["isOpenAccess"] = True
        result["source"] = "doaj"

        return result

    @staticmethod
    def _extract_doaj_authors(
        authors_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract author information from DOAJ data."""
        authors = []

        for author in authors_data:
            author_info = {
                "name": author.get("name", ""),
                "authorId": None,
                "orcid": author.get("orcid_id"),
                "affiliation": author.get("affiliation"),
                "gsProfileUrl": None,
            }

            if author_info["name"]:
                authors.append(author_info)

        return authors

    @staticmethod
    def parse_base_paper(paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse BASE search result data to standardized format.

        Args:
            paper: BASE document dictionary

        Returns:
            Standardized paper dictionary
        """
        result = {}

        # Basic fields from Dublin Core metadata
        if "dctitle" in paper:
            # dctitle can be a list or string
            title = paper["dctitle"]
            if isinstance(title, list):
                result["title"] = title[0] if title else ""
            else:
                result["title"] = title

        if "dcdescription" in paper:
            description = paper["dcdescription"]
            if isinstance(description, list):
                result["abstract"] = description[0] if description else ""
            else:
                result["abstract"] = description

        # Extract identifiers
        if "dcidentifier" in paper:
            identifiers = paper["dcidentifier"]
            if isinstance(identifiers, list):
                for identifier in identifiers:
                    if "doi.org" in identifier:
                        result["doi"] = identifier.split("doi.org/")[-1]
                        break
            elif "doi.org" in identifiers:
                result["doi"] = identifiers.split("doi.org/")[-1]

        # Extract authors
        if "dccreator" in paper:
            result["authors"] = JSONParser._extract_base_authors(paper["dccreator"])

        # Extract date
        if "dcdate" in paper:
            date = paper["dcdate"]
            if isinstance(date, list):
                result["publicationDate"] = date[0] if date else ""
            else:
                result["publicationDate"] = date

        # Extract year
        if "dcyear" in paper:
            year = paper["dcyear"]
            if isinstance(year, list):
                year = year[0] if year else ""
            if year and not result.get("publicationDate"):
                result["publicationDate"] = f"{year}-01-01"

        # Extract language
        if "dclanguage" in paper:
            language = paper["dclanguage"]
            if isinstance(language, list):
                result["language"] = language[0] if language else ""
            else:
                result["language"] = language

        # Extract type
        if "dctype" in paper:
            doc_type = paper["dctype"]
            if isinstance(doc_type, list):
                result["type"] = doc_type[0] if doc_type else ""
            else:
                result["type"] = doc_type

        # Extract subjects
        if "dcsubject" in paper:
            subjects = paper["dcsubject"]
            if isinstance(subjects, list):
                result["subjects"] = subjects
            else:
                result["subjects"] = [subjects]

        # Extract publisher
        if "dcpublisher" in paper:
            publisher = paper["dcpublisher"]
            if isinstance(publisher, list):
                result["publisher"] = publisher[0] if publisher else ""
            else:
                result["publisher"] = publisher

        # Extract source/collection
        if "dcsource" in paper:
            source = paper["dcsource"]
            if isinstance(source, list):
                result["venueName"] = source[0] if source else ""
            else:
                result["venueName"] = source

        # Extract open access status
        if "oa" in paper:
            result["isOpenAccess"] = (
                paper["oa"] == 1 or paper["oa"] == "1" or paper["oa"] is True
            )

        # Extract repository/collection info
        if "collection" in paper:
            result["repository"] = paper["collection"]

        result["source"] = "base"

        return result

    @staticmethod
    def _extract_base_authors(authors_data) -> List[Dict[str, Any]]:
        """Extract author information from BASE data."""
        authors = []

        if isinstance(authors_data, list):
            for author in authors_data:
                if isinstance(author, str):
                    authors.append(
                        {
                            "name": author.strip(),
                            "authorId": None,
                            "orcid": None,
                            "affiliation": None,
                            "gsProfileUrl": None,
                        }
                    )
        elif isinstance(authors_data, str):
            # Sometimes authors come as a semicolon or comma-separated string
            separators = [";", ",", " and ", " & "]
            author_names = [authors_data]

            for sep in separators:
                if sep in authors_data:
                    author_names = authors_data.split(sep)
                    break

            for name in author_names:
                name = name.strip()
                if name:
                    authors.append(
                        {
                            "name": name,
                            "authorId": None,
                            "orcid": None,
                            "affiliation": None,
                            "gsProfileUrl": None,
                        }
                    )

        return authors
