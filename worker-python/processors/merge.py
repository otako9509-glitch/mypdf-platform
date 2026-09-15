import os
from typing import List
from pypdf import PdfReader, PdfWriter


def merge_pdfs(input_files: List[str], output_path: str) -> bool:
    """
    Merge multiple PDF files into a single PDF.
    
    Args:
        input_files: List of paths to PDF files to merge
        output_path: Path where the merged PDF will be saved
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not input_files:
            raise ValueError("No input files provided")
        
        if not os.path.exists(output_path):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        writer = PdfWriter()
        total_pages = 0
        
        for file_path in input_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Input file not found: {file_path}")
            
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
            
            if page_count == 0:
                print(f"Warning: File {file_path} has no pages, skipping")
                continue
            
            # Add all pages from this PDF
            for page in reader.pages:
                writer.add_page(page)
            
            total_pages += page_count
            print(f"Added {page_count} pages from {os.path.basename(file_path)}")
        
        if total_pages == 0:
            raise ValueError("No pages were added to the merged PDF")
        
        # Write the merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully merged {len(input_files)} files into {total_pages} pages")
        return True
        
    except Exception as e:
        print(f"Error merging PDFs: {str(e)}")
        raise e
