"""Tests for XML parser and splitting validator."""
import pytest
from pathlib import Path
from modules.validators import (
    parse_splitted_result_xml,
    SplitDocumentInfo,
    SplittingValidator,
    DocumentMatch,
)
from modules.types import DocumentType, DocumentInstance, ProcessingResult, PageClassification


class TestXMLParser:
    """Tests for XML parsing functionality."""
    
    def test_parse_simple_xml(self, tmp_path):
        """Test parsing a simple XML file."""
        xml_content = """<?xml version='1.0' encoding='UTF-8' ?>
<SplittedResult>
 <ParentComId>test123</ParentComId>
 <Owner>TEST</Owner>
 <User>TESTUSER</User>
 <FilePath>\\test\\path.PDF</FilePath>
 <SplittedDocs>
  <SplitDoc>
   <Entname>CFIFILEM</Entname>
   <PrimaryNum>12345</PrimaryNum>
   <DocType>FSI</DocType>
   <ProcessedFile>\\test\\output.pdf</ProcessedFile>
   <Pages>
    <Page>
     <PageNum>1</PageNum>
     <Rotate>0</Rotate>
    </Page>
   </Pages>
   <References/>
   <FilingComId>abc123</FilingComId>
   <FilingFileRef>TEST-001</FilingFileRef>
   <FilingDesc>Supplier Invoice</FilingDesc>
   <User>TESTUSER</User>
   <Owner>TEST</Owner>
   <FilingMessage>Document successfully scanned</FilingMessage>
   <FilingDocTypeCode>FSI</FilingDocTypeCode>
   <FilingDocTypeName>Supplier Invoice</FilingDocTypeName>
  </SplitDoc>
 </SplittedDocs>
</SplittedResult>"""
        
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding='utf-8')
        
        result = parse_splitted_result_xml(str(xml_file))
        
        assert result.parent_com_id == "test123"
        assert result.owner == "TEST"
        assert result.user == "TESTUSER"
        assert result.total_documents == 1
        assert len(result.split_docs) == 1
        
        doc = result.split_docs[0]
        assert doc.doc_type == "FSI"
        assert doc.primary_num == "12345"
        assert doc.filing_doc_type_name == "Supplier Invoice"
        assert doc.page_count == 1
        assert doc.page_numbers == [1]
    
    def test_parse_multi_page_document(self, tmp_path):
        """Test parsing document with multiple pages."""
        xml_content = """<?xml version='1.0' encoding='UTF-8' ?>
<SplittedResult>
 <ParentComId>test123</ParentComId>
 <Owner>TEST</Owner>
 <User>TESTUSER</User>
 <FilePath>\\test\\path.PDF</FilePath>
 <SplittedDocs>
  <SplitDoc>
   <Entname>CFIFILEM</Entname>
   <PrimaryNum>12345</PrimaryNum>
   <DocType>FPL</DocType>
   <ProcessedFile>\\test\\output.pdf</ProcessedFile>
   <Pages>
    <Page>
     <PageNum>1</PageNum>
     <Rotate>0</Rotate>
    </Page>
    <Page>
     <PageNum>2</PageNum>
     <Rotate>0</Rotate>
    </Page>
    <Page>
     <PageNum>3</PageNum>
     <Rotate>0</Rotate>
    </Page>
   </Pages>
   <References/>
   <FilingComId>abc123</FilingComId>
   <FilingFileRef>TEST-001</FilingFileRef>
   <FilingDesc>Packing List</FilingDesc>
   <User>TESTUSER</User>
   <Owner>TEST</Owner>
   <FilingMessage>Document successfully scanned</FilingMessage>
   <FilingDocTypeCode>FPL</FilingDocTypeCode>
   <FilingDocTypeName>Packing List</FilingDocTypeName>
  </SplitDoc>
 </SplittedDocs>
</SplittedResult>"""
        
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding='utf-8')
        
        result = parse_splitted_result_xml(str(xml_file))
        
        assert result.total_documents == 1
        doc = result.split_docs[0]
        assert doc.page_count == 3
        assert doc.page_numbers == [1, 2, 3]
        assert doc.start_page == 1
        assert doc.end_page == 3
    
    def test_parse_multiple_documents(self, tmp_path):
        """Test parsing multiple split documents."""
        xml_content = """<?xml version='1.0' encoding='UTF-8' ?>
<SplittedResult>
 <ParentComId>test123</ParentComId>
 <Owner>TEST</Owner>
 <User>TESTUSER</User>
 <FilePath>\\test\\path.PDF</FilePath>
 <SplittedDocs>
  <SplitDoc>
   <DocType>FSI</DocType>
   <PrimaryNum>12345</PrimaryNum>
   <Pages>
    <Page>
     <PageNum>1</PageNum>
     <Rotate>0</Rotate>
    </Page>
   </Pages>
   <FilingDocTypeCode>FSI</FilingDocTypeCode>
   <FilingDocTypeName>Supplier Invoice</FilingDocTypeName>
  </SplitDoc>
  <SplitDoc>
   <DocType>FPL</DocType>
   <PrimaryNum>12345</PrimaryNum>
   <Pages>
    <Page>
     <PageNum>2</PageNum>
     <Rotate>0</Rotate>
    </Page>
   </Pages>
   <FilingDocTypeCode>FPL</FilingDocTypeCode>
   <FilingDocTypeName>Packing List</FilingDocTypeName>
  </SplitDoc>
 </SplittedDocs>
</SplittedResult>"""
        
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding='utf-8')
        
        result = parse_splitted_result_xml(str(xml_file))
        
        assert result.total_documents == 2
        assert result.split_docs[0].filing_doc_type_name == "Supplier Invoice"
        assert result.split_docs[1].filing_doc_type_name == "Packing List"
        
        type_counts = result.get_documents_by_type()
        assert type_counts["Supplier Invoice"] == 1
        assert type_counts["Packing List"] == 1


class TestSplittingValidator:
    """Tests for splitting validator."""
    
    def test_perfect_match(self):
        """Test validation with perfect match."""
        # Create predicted documents
        predicted_docs = [
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=1,
                end_page=1,
                page_numbers=[1]
            ),
            DocumentInstance(
                document_type=DocumentType.PACKING_LIST,
                start_page=2,
                end_page=2,
                page_numbers=[2]
            ),
        ]
        
        # Create processing result
        processing_result = ProcessingResult(
            pdf_path="test.pdf",
            total_pages=2,
            classifications=[
                PageClassification(1, DocumentType.INVOICE),
                PageClassification(2, DocumentType.PACKING_LIST),
            ],
            extractions=[],
            validations=[],
            document_instances=predicted_docs
        )
        
        # Create ground truth (simulating parsed XML)
        from modules.validators.xml_parser import SplittedResultInfo, SplitDocumentInfo, PageInfo
        
        gt_docs = [
            SplitDocumentInfo(
                doc_type="FSI",
                primary_num="12345",
                pages=[PageInfo(page_num=1, rotate=0)],
                filing_doc_type_code="FSI",
                filing_doc_type_name="Supplier Invoice"
            ),
            SplitDocumentInfo(
                doc_type="FPL",
                primary_num="12345",
                pages=[PageInfo(page_num=2, rotate=0)],
                filing_doc_type_code="FPL",
                filing_doc_type_name="Packing List"
            ),
        ]
        
        ground_truth = SplittedResultInfo(
            parent_com_id="test",
            owner="TEST",
            user="TESTUSER",
            file_path="test.pdf",
            split_docs=gt_docs
        )
        
        # Validate
        validator = SplittingValidator()
        result = validator.validate(processing_result, ground_truth)
        
        assert result.document_count_match is True
        assert result.total_documents_predicted == 2
        assert result.total_documents_ground_truth == 2
        assert result.document_type_accuracy == 100.0
        assert result.page_count_accuracy == 100.0
        assert result.page_numbers_accuracy == 100.0
        assert result.overall_score == 100.0
        
        # Check individual matches
        assert len(result.matches) == 2
        assert all(m.exact_match for m in result.matches)
    
    def test_type_mismatch(self):
        """Test validation with document type mismatch."""
        # Create predicted documents (wrong type)
        predicted_docs = [
            DocumentInstance(
                document_type=DocumentType.PACKING_LIST,  # Wrong!
                start_page=1,
                end_page=1,
                page_numbers=[1]
            ),
        ]
        
        processing_result = ProcessingResult(
            pdf_path="test.pdf",
            total_pages=1,
            classifications=[PageClassification(1, DocumentType.PACKING_LIST)],
            extractions=[],
            validations=[],
            document_instances=predicted_docs
        )
        
        from modules.validators.xml_parser import SplittedResultInfo, SplitDocumentInfo, PageInfo
        
        gt_docs = [
            SplitDocumentInfo(
                doc_type="FSI",
                primary_num="12345",
                pages=[PageInfo(page_num=1, rotate=0)],
                filing_doc_type_code="FSI",
                filing_doc_type_name="Supplier Invoice"
            ),
        ]
        
        ground_truth = SplittedResultInfo(
            parent_com_id="test",
            owner="TEST",
            user="TESTUSER",
            file_path="test.pdf",
            split_docs=gt_docs
        )
        
        validator = SplittingValidator()
        result = validator.validate(processing_result, ground_truth)
        
        assert result.document_type_accuracy == 0.0
        assert result.page_count_accuracy == 100.0  # Page count is still correct
        assert result.page_numbers_accuracy == 100.0  # Page numbers are still correct
        assert result.overall_score < 100.0
        
        assert result.matches[0].type_match is False
        assert result.matches[0].page_count_match is True
        assert result.matches[0].exact_match is False
    
    def test_page_count_mismatch(self):
        """Test validation with page count mismatch."""
        # Predicted: 2 pages, Ground truth: 3 pages
        predicted_docs = [
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=1,
                end_page=2,
                page_numbers=[1, 2]
            ),
        ]
        
        processing_result = ProcessingResult(
            pdf_path="test.pdf",
            total_pages=2,
            classifications=[
                PageClassification(1, DocumentType.INVOICE),
                PageClassification(2, DocumentType.INVOICE),
            ],
            extractions=[],
            validations=[],
            document_instances=predicted_docs
        )
        
        from modules.validators.xml_parser import SplittedResultInfo, SplitDocumentInfo, PageInfo
        
        gt_docs = [
            SplitDocumentInfo(
                doc_type="FSI",
                primary_num="12345",
                pages=[
                    PageInfo(page_num=1, rotate=0),
                    PageInfo(page_num=2, rotate=0),
                    PageInfo(page_num=3, rotate=0),
                ],
                filing_doc_type_code="FSI",
                filing_doc_type_name="Supplier Invoice"
            ),
        ]
        
        ground_truth = SplittedResultInfo(
            parent_com_id="test",
            owner="TEST",
            user="TESTUSER",
            file_path="test.pdf",
            split_docs=gt_docs
        )
        
        validator = SplittingValidator()
        result = validator.validate(processing_result, ground_truth)
        
        assert result.document_type_accuracy == 100.0
        assert result.page_count_accuracy == 0.0
        assert result.page_numbers_accuracy == 0.0
        
        assert result.matches[0].type_match is True
        assert result.matches[0].page_count_match is False
        assert result.matches[0].exact_match is False
    
    def test_missing_predicted_document(self):
        """Test when predicted documents are fewer than ground truth."""
        # Only 1 predicted, but 2 in ground truth
        predicted_docs = [
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=1,
                end_page=1,
                page_numbers=[1]
            ),
        ]
        
        processing_result = ProcessingResult(
            pdf_path="test.pdf",
            total_pages=1,
            classifications=[PageClassification(1, DocumentType.INVOICE)],
            extractions=[],
            validations=[],
            document_instances=predicted_docs
        )
        
        from modules.validators.xml_parser import SplittedResultInfo, SplitDocumentInfo, PageInfo
        
        gt_docs = [
            SplitDocumentInfo(
                doc_type="FSI",
                primary_num="12345",
                pages=[PageInfo(page_num=1, rotate=0)],
                filing_doc_type_code="FSI",
                filing_doc_type_name="Supplier Invoice"
            ),
            SplitDocumentInfo(
                doc_type="FPL",
                primary_num="12345",
                pages=[PageInfo(page_num=2, rotate=0)],
                filing_doc_type_code="FPL",
                filing_doc_type_name="Packing List"
            ),
        ]
        
        ground_truth = SplittedResultInfo(
            parent_com_id="test",
            owner="TEST",
            user="TESTUSER",
            file_path="test.pdf",
            split_docs=gt_docs
        )
        
        validator = SplittingValidator()
        result = validator.validate(processing_result, ground_truth)
        
        assert result.document_count_match is False
        assert result.total_documents_predicted == 1
        assert result.total_documents_ground_truth == 2
        assert len(result.matches) == 2
        
        # First match should be good
        assert result.matches[0].predicted_doc is not None
        assert result.matches[0].ground_truth_doc is not None
        
        # Second match should have missing predicted
        assert result.matches[1].predicted_doc is None
        assert result.matches[1].ground_truth_doc is not None
    
    def test_generate_report(self):
        """Test report generation."""
        predicted_docs = [
            DocumentInstance(
                document_type=DocumentType.INVOICE,
                start_page=1,
                end_page=1,
                page_numbers=[1]
            ),
        ]
        
        processing_result = ProcessingResult(
            pdf_path="test.pdf",
            total_pages=1,
            classifications=[PageClassification(1, DocumentType.INVOICE)],
            extractions=[],
            validations=[],
            document_instances=predicted_docs
        )
        
        from modules.validators.xml_parser import SplittedResultInfo, SplitDocumentInfo, PageInfo
        
        gt_docs = [
            SplitDocumentInfo(
                doc_type="FSI",
                primary_num="12345",
                pages=[PageInfo(page_num=1, rotate=0)],
                filing_doc_type_code="FSI",
                filing_doc_type_name="Supplier Invoice"
            ),
        ]
        
        ground_truth = SplittedResultInfo(
            parent_com_id="test",
            owner="TEST",
            user="TESTUSER",
            file_path="test.pdf",
            split_docs=gt_docs
        )
        
        validator = SplittingValidator()
        result = validator.validate(processing_result, ground_truth)
        report = validator.generate_report(result)
        
        # Check that report contains key information
        assert "PDF Splitting Validation Report" in report
        assert "Predicted Documents: 1" in report
        assert "Ground Truth Documents: 1" in report
        assert "Overall Score: 100.0%" in report
        assert "Document Type Accuracy: 100.0%" in report
