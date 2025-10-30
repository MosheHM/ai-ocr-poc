"""Validator for PDF splitting results against XML ground truth."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from modules.types import ProcessingResult, DocumentInstance, DocumentType
from modules.validators.xml_parser import SplittedResultInfo, SplitDocumentInfo


# Mapping from XML DocType codes to our DocumentType enum
DOCTYPE_MAPPING = {
    'FSI': DocumentType.INVOICE,  # Supplier Invoice
    'FPL': DocumentType.PACKING_LIST,  # Packing List
    'OBL': DocumentType.OBL,  # Ocean Bill of Lading
    'HAWB': DocumentType.HAWB,  # House Air Waybill
    'FWA': DocumentType.HAWB,  # Waybill (map to HAWB as closest match)
}

# Reverse mapping for display
DOCTYPE_NAME_MAPPING = {
    'Supplier Invoice': DocumentType.INVOICE,
    'Packing List': DocumentType.PACKING_LIST,
    'Ocean Bill of Lading': DocumentType.OBL,
    'House Air Waybill': DocumentType.HAWB,
    'Waybill': DocumentType.HAWB,  # Map to HAWB as closest match
}


@dataclass
class DocumentMatch:
    """Result of matching a predicted document with ground truth."""
    predicted_doc: Optional[DocumentInstance]
    ground_truth_doc: Optional[SplitDocumentInfo]
    type_match: bool
    page_count_match: bool
    page_numbers_match: bool
    exact_match: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'predicted': {
                'type': self.predicted_doc.document_type.value if self.predicted_doc else None,
                'pages': self.predicted_doc.page_numbers if self.predicted_doc else None,
                'page_range': self.predicted_doc.page_range if self.predicted_doc else None,
            } if self.predicted_doc else None,
            'ground_truth': {
                'type': self.ground_truth_doc.filing_doc_type_name if self.ground_truth_doc else None,
                'pages': self.ground_truth_doc.page_numbers if self.ground_truth_doc else None,
            } if self.ground_truth_doc else None,
            'type_match': self.type_match,
            'page_count_match': self.page_count_match,
            'page_numbers_match': self.page_numbers_match,
            'exact_match': self.exact_match,
        }


@dataclass
class SplittingValidationResult:
    """Result of validating PDF splitting against XML ground truth."""
    total_documents_predicted: int
    total_documents_ground_truth: int
    document_count_match: bool
    matches: List[DocumentMatch]
    document_type_accuracy: float
    page_count_accuracy: float
    page_numbers_accuracy: float
    overall_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            'total_documents_predicted': self.total_documents_predicted,
            'total_documents_ground_truth': self.total_documents_ground_truth,
            'document_count_match': self.document_count_match,
            'document_type_accuracy': self.document_type_accuracy,
            'page_count_accuracy': self.page_count_accuracy,
            'page_numbers_accuracy': self.page_numbers_accuracy,
            'overall_score': self.overall_score,
            'matches': [m.to_dict() for m in self.matches],
        }


def map_doctype_code_to_enum(code: str) -> Optional[DocumentType]:
    """Map XML DocType code to DocumentType enum."""
    return DOCTYPE_MAPPING.get(code)


def map_doctype_name_to_enum(name: str) -> Optional[DocumentType]:
    """Map XML DocType name to DocumentType enum."""
    return DOCTYPE_NAME_MAPPING.get(name)


class SplittingValidator:
    """Validates PDF splitting results against XML ground truth."""
    
    def validate(
        self,
        processing_result: ProcessingResult,
        ground_truth: SplittedResultInfo
    ) -> SplittingValidationResult:
        """
        Validate splitting results against ground truth.
        
        Args:
            processing_result: Result from AI processing
            ground_truth: Parsed XML ground truth
            
        Returns:
            SplittingValidationResult with detailed comparison
        """
        predicted_docs = processing_result.document_instances
        gt_docs = ground_truth.split_docs
        
        # Match documents
        matches = self._match_documents(predicted_docs, gt_docs)
        
        # Calculate metrics
        total_predicted = len(predicted_docs)
        total_gt = len(gt_docs)
        document_count_match = total_predicted == total_gt
        
        # Calculate accuracy scores
        if len(matches) == 0:
            type_accuracy = 0.0
            page_count_accuracy = 0.0
            page_numbers_accuracy = 0.0
        else:
            type_accuracy = sum(1 for m in matches if m.type_match) / len(matches) * 100
            page_count_accuracy = sum(1 for m in matches if m.page_count_match) / len(matches) * 100
            page_numbers_accuracy = sum(1 for m in matches if m.page_numbers_match) / len(matches) * 100
        
        # Overall score is weighted average
        overall_score = (
            type_accuracy * 0.4 +  # Type is most important
            page_count_accuracy * 0.3 +  # Page count is important
            page_numbers_accuracy * 0.3  # Exact page numbers
        )
        
        return SplittingValidationResult(
            total_documents_predicted=total_predicted,
            total_documents_ground_truth=total_gt,
            document_count_match=document_count_match,
            matches=matches,
            document_type_accuracy=type_accuracy,
            page_count_accuracy=page_count_accuracy,
            page_numbers_accuracy=page_numbers_accuracy,
            overall_score=overall_score,
        )
    
    def _match_documents(
        self,
        predicted_docs: List[DocumentInstance],
        gt_docs: List[SplitDocumentInfo]
    ) -> List[DocumentMatch]:
        """
        Match predicted documents with ground truth documents.
        
        This uses a simple sequential matching strategy since documents
        are typically processed in page order.
        """
        matches: List[DocumentMatch] = []
        
        # Match by index (assumes both lists are in page order)
        max_len = max(len(predicted_docs), len(gt_docs))
        
        for i in range(max_len):
            pred_doc = predicted_docs[i] if i < len(predicted_docs) else None
            gt_doc = gt_docs[i] if i < len(gt_docs) else None
            
            if pred_doc is None and gt_doc is None:
                continue
            
            # Check type match
            type_match = False
            if pred_doc and gt_doc:
                # Try to map GT doc type to our enum
                gt_type = map_doctype_name_to_enum(gt_doc.filing_doc_type_name)
                if gt_type is None:
                    gt_type = map_doctype_code_to_enum(gt_doc.doc_type)
                
                if gt_type:
                    type_match = pred_doc.document_type == gt_type
            
            # Check page count match
            page_count_match = False
            if pred_doc and gt_doc:
                page_count_match = len(pred_doc.page_numbers) == gt_doc.page_count
            
            # Check page numbers match
            page_numbers_match = False
            if pred_doc and gt_doc:
                # Sort both lists for comparison
                pred_pages = sorted(pred_doc.page_numbers)
                gt_pages = sorted(gt_doc.page_numbers)
                page_numbers_match = pred_pages == gt_pages
            
            exact_match = type_match and page_count_match and page_numbers_match
            
            match = DocumentMatch(
                predicted_doc=pred_doc,
                ground_truth_doc=gt_doc,
                type_match=type_match,
                page_count_match=page_count_match,
                page_numbers_match=page_numbers_match,
                exact_match=exact_match,
            )
            matches.append(match)
        
        return matches
    
    def generate_report(self, result: SplittingValidationResult) -> str:
        """Generate a human-readable report of validation results."""
        lines = []
        lines.append("PDF Splitting Validation Report")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        lines.append("Summary:")
        lines.append(f"  Predicted Documents: {result.total_documents_predicted}")
        lines.append(f"  Ground Truth Documents: {result.total_documents_ground_truth}")
        lines.append(f"  Document Count Match: {'✓' if result.document_count_match else '✗'}")
        lines.append("")
        
        # Accuracy metrics
        lines.append("Accuracy Metrics:")
        lines.append(f"  Document Type Accuracy: {result.document_type_accuracy:.1f}%")
        lines.append(f"  Page Count Accuracy: {result.page_count_accuracy:.1f}%")
        lines.append(f"  Page Numbers Accuracy: {result.page_numbers_accuracy:.1f}%")
        lines.append(f"  Overall Score: {result.overall_score:.1f}%")
        lines.append("")
        
        # Document-by-document comparison
        lines.append("Document-by-Document Comparison:")
        lines.append("-" * 80)
        
        for i, match in enumerate(result.matches, 1):
            lines.append(f"\nDocument #{i}:")
            
            if match.predicted_doc:
                lines.append(f"  Predicted: {match.predicted_doc.document_type.value}")
                lines.append(f"    Pages: {match.predicted_doc.page_range} ({match.predicted_doc.page_numbers})")
            else:
                lines.append(f"  Predicted: MISSING")
            
            if match.ground_truth_doc:
                lines.append(f"  Ground Truth: {match.ground_truth_doc.filing_doc_type_name}")
                lines.append(f"    Pages: {match.ground_truth_doc.page_numbers}")
            else:
                lines.append(f"  Ground Truth: MISSING")
            
            lines.append(f"  Type Match: {'✓' if match.type_match else '✗'}")
            lines.append(f"  Page Count Match: {'✓' if match.page_count_match else '✗'}")
            lines.append(f"  Page Numbers Match: {'✓' if match.page_numbers_match else '✗'}")
            lines.append(f"  Exact Match: {'✓' if match.exact_match else '✗'}")
        
        return "\n".join(lines)
