"""Parser for SplittedResult XML ground truth files."""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PageInfo:
    """Information about a page in a split document."""
    page_num: int
    rotate: int


@dataclass
class SplitDocumentInfo:
    """Information about a split document from XML."""
    doc_type: str
    primary_num: str
    pages: List[PageInfo]
    filing_doc_type_code: str
    filing_doc_type_name: str
    
    @property
    def page_count(self) -> int:
        """Get the number of pages in this document."""
        return len(self.pages)
    
    @property
    def page_numbers(self) -> List[int]:
        """Get list of page numbers."""
        return [p.page_num for p in self.pages]
    
    @property
    def start_page(self) -> int:
        """Get the first page number."""
        return min(self.page_numbers) if self.pages else 0
    
    @property
    def end_page(self) -> int:
        """Get the last page number."""
        return max(self.page_numbers) if self.pages else 0


@dataclass
class SplittedResultInfo:
    """Information from a SplittedResult XML file."""
    parent_com_id: str
    owner: str
    user: str
    file_path: str
    split_docs: List[SplitDocumentInfo]
    
    @property
    def total_documents(self) -> int:
        """Get total number of split documents."""
        return len(self.split_docs)
    
    def get_documents_by_type(self) -> Dict[str, int]:
        """Get count of documents by type."""
        type_counts: Dict[str, int] = {}
        for doc in self.split_docs:
            doc_type = doc.filing_doc_type_name
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        return type_counts


def parse_splitted_result_xml(xml_path: str) -> SplittedResultInfo:
    """
    Parse a SplittedResult XML file.
    
    Args:
        xml_path: Path to the XML file
        
    Returns:
        SplittedResultInfo object with parsed data
        
    Raises:
        FileNotFoundError: If XML file doesn't exist
        ET.ParseError: If XML is malformed
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Parse top-level fields
    parent_com_id = root.findtext('ParentComId', '')
    owner = root.findtext('Owner', '')
    user = root.findtext('User', '')
    file_path = root.findtext('FilePath', '')
    
    # Parse split documents
    split_docs: List[SplitDocumentInfo] = []
    splitted_docs_elem = root.find('SplittedDocs')
    
    if splitted_docs_elem is not None:
        for split_doc_elem in splitted_docs_elem.findall('SplitDoc'):
            # Parse basic fields
            doc_type = split_doc_elem.findtext('DocType', '')
            primary_num = split_doc_elem.findtext('PrimaryNum', '')
            filing_doc_type_code = split_doc_elem.findtext('FilingDocTypeCode', '')
            filing_doc_type_name = split_doc_elem.findtext('FilingDocTypeName', '')
            
            # Parse pages
            pages: List[PageInfo] = []
            pages_elem = split_doc_elem.find('Pages')
            if pages_elem is not None:
                for page_elem in pages_elem.findall('Page'):
                    page_num_str = page_elem.findtext('PageNum', '0')
                    rotate_str = page_elem.findtext('Rotate', '0')
                    
                    try:
                        page_num = int(page_num_str)
                        rotate = int(rotate_str)
                        pages.append(PageInfo(page_num=page_num, rotate=rotate))
                    except ValueError:
                        # Skip invalid page numbers
                        continue
            
            split_doc = SplitDocumentInfo(
                doc_type=doc_type,
                primary_num=primary_num,
                pages=pages,
                filing_doc_type_code=filing_doc_type_code,
                filing_doc_type_name=filing_doc_type_name
            )
            split_docs.append(split_doc)
    
    return SplittedResultInfo(
        parent_com_id=parent_com_id,
        owner=owner,
        user=user,
        file_path=file_path,
        split_docs=split_docs
    )
