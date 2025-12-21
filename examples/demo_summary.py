#!/usr/bin/env python
"""Demonstration of the enhanced document summary functionality.

This script shows how the system now provides clear summaries of:
1. How many documents of each type are in a PDF
2. Which pages each document occupies
"""

from modules.types import (
    DocumentType, 
    PageClassification, 
    ProcessingResult,
    ExtractionResult
)
from modules.utils import group_pages_into_documents
from collections import Counter


def demonstrate_document_summary():
    """Demonstrate the document summary functionality with a sample scenario."""
    
    print("=" * 80)
    print("DEMONSTRATION: Enhanced Document Summary")
    print("=" * 80)
    print()
    
    # Scenario: A 10-page PDF with alternating invoices and packing lists
    print("Scenario: Processing a 10-page PDF")
    print("-" * 80)
    print()
    
    # Simulate page classifications from the AI classifier
    classifications = [
        # Invoice 1: pages 1-3
        PageClassification(page_number=1, document_type=DocumentType.INVOICE, confidence=0.95),
        PageClassification(page_number=2, document_type=DocumentType.INVOICE, confidence=0.93),
        PageClassification(page_number=3, document_type=DocumentType.INVOICE, confidence=0.97),
        # Packing List 1: page 4
        PageClassification(page_number=4, document_type=DocumentType.PACKING_LIST, confidence=0.94),
        # Invoice 2: pages 5-6
        PageClassification(page_number=5, document_type=DocumentType.INVOICE, confidence=0.96),
        PageClassification(page_number=6, document_type=DocumentType.INVOICE, confidence=0.95),
        # Packing List 2: pages 7-9
        PageClassification(page_number=7, document_type=DocumentType.PACKING_LIST, confidence=0.98),
        PageClassification(page_number=8, document_type=DocumentType.PACKING_LIST, confidence=0.97),
        PageClassification(page_number=9, document_type=DocumentType.PACKING_LIST, confidence=0.96),
        # Invoice 3: page 10
        PageClassification(page_number=10, document_type=DocumentType.INVOICE, confidence=0.99),
    ]
    
    # Group pages into document instances
    document_instances = group_pages_into_documents(classifications)
    
    # Create a ProcessingResult (simulated)
    result = ProcessingResult(
        pdf_path="sample_document.pdf",
        total_pages=10,
        classifications=classifications,
        extractions=[],  # Would be populated in real scenario
        validations=[],
        document_instances=document_instances
    )
    
    # Display the summary
    print("Document Summary:")
    print("-" * 80)
    
    # Count documents by type
    doc_type_counts = Counter(doc.document_type for doc in result.document_instances)
    
    # Display counts
    for doc_type, count in doc_type_counts.items():
        print(f"  {doc_type.value}: {count} document(s)")
    
    print()
    print("Document Instances (showing page ranges):")
    
    # Number each document instance
    for i, doc_instance in enumerate(result.document_instances, 1):
        page_info = f"page {doc_instance.page_range}" if doc_instance.start_page == doc_instance.end_page else f"pages {doc_instance.page_range}"
        print(f"  {i}. {doc_instance.document_type.value} - {page_info}")
    
    print()
    print("=" * 80)
    print()
    
    # Show how this would appear in JSON output
    print("JSON Output Format:")
    print("-" * 80)
    
    import json
    
    # Simulate JSON output
    json_output = {
        "pdf_path": result.pdf_path,
        "total_pages": result.total_pages,
        "document_summary": {
            "total_documents": len(result.document_instances),
            "documents_by_type": dict(doc_type_counts)
        },
        "document_instances": [
            {
                "document_type": doc.document_type.value,
                "start_page": doc.start_page,
                "end_page": doc.end_page,
                "page_count": len(doc.page_numbers),
                "page_range": doc.page_range
            }
            for doc in result.document_instances
        ]
    }
    
    print(json.dumps(json_output, indent=2))
    print()
    print("=" * 80)
    print()
    
    # Show the breakdown
    print("Summary:")
    print("-" * 80)
    print(f"✓ Found {len(result.document_instances)} document instances in {result.total_pages} pages")
    print(f"✓ Invoices: {doc_type_counts[DocumentType.INVOICE]}")
    print(f"✓ Packing Lists: {doc_type_counts[DocumentType.PACKING_LIST]}")
    print()
    print("Example use case from problem statement:")
    print("  'One PDF with 10 pages including 3 invoices and 2 packing lists'")
    print("  ✓ Invoice 1: pages 1-3")
    print("  ✓ Packing List 1: page 4")
    print("  ✓ Invoice 2: pages 5-6")
    print("  ✓ Packing List 2: pages 7-9")
    print("  ✓ Invoice 3: page 10")
    print()
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_document_summary()
