"""Utility functions for grouping pages into document instances."""
from typing import List
from modules.types import PageClassification, DocumentInstance, DocumentType


def group_pages_into_documents(
    classifications: List[PageClassification]
) -> List[DocumentInstance]:
    """Group consecutive pages of the same type into document instances.
    
    For example, if pages 1-2 are classified as Invoice and pages 3-5 as Packing List,
    this will return two DocumentInstance objects:
    - DocumentInstance(type=Invoice, pages=[1, 2])
    - DocumentInstance(type=PackingList, pages=[3, 4, 5])
    
    Args:
        classifications: List of page classifications
    
    Returns:
        List of DocumentInstance objects
    """
    if not classifications:
        return []
    
    documents = []
    current_type = classifications[0].document_type
    current_pages = [classifications[0].page_number]
    
    for i in range(1, len(classifications)):
        cls = classifications[i]
        
        # Check if this page is the same type as the current group
        if cls.document_type == current_type:
            # Add to current group
            current_pages.append(cls.page_number)
        else:
            # Different type - save current group and start new one
            documents.append(DocumentInstance(
                document_type=current_type,
                start_page=current_pages[0],
                end_page=current_pages[-1],
                page_numbers=current_pages
            ))
            
            # Start new group
            current_type = cls.document_type
            current_pages = [cls.page_number]
    
    # Don't forget the last group
    documents.append(DocumentInstance(
        document_type=current_type,
        start_page=current_pages[0],
        end_page=current_pages[-1],
        page_numbers=current_pages
    ))
    
    return documents
