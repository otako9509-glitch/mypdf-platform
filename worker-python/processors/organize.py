import os
from typing import List
from pypdf import PdfReader, PdfWriter


def organize_pdf(input_file: str, output_path: str, page_order: List[int]) -> bool:
    """
    Reorder PDF pages according to specified order.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the organized PDF will be saved
        page_order: List of page numbers (1-indexed) in desired order
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not page_order:
            raise ValueError("Page order cannot be empty")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        reader = PdfReader(input_file)
        total_pages = len(reader.pages)
        
        # Validate page numbers
        for page_num in page_order:
            if page_num < 1 or page_num > total_pages:
                raise ValueError(f"Invalid page number: {page_num}. Must be between 1 and {total_pages}")
        
        writer = PdfWriter()
        
        # Add pages in specified order
        for page_num in page_order:
            writer.add_page(reader.pages[page_num - 1])
        
        # Write the organized PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully organized PDF with {len(page_order)} pages")
        return True
        
    except Exception as e:
        print(f"Error organizing PDF: {str(e)}")
        raise e


def delete_pages(input_file: str, output_path: str, pages_to_delete: List[int]) -> bool:
    """
    Delete specific pages from PDF.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the modified PDF will be saved
        pages_to_delete: List of page numbers (1-indexed) to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        reader = PdfReader(input_file)
        total_pages = len(reader.pages)
        
        # Validate page numbers
        for page_num in pages_to_delete:
            if page_num < 1 or page_num > total_pages:
                raise ValueError(f"Invalid page number: {page_num}. Must be between 1 and {total_pages}")
        
        writer = PdfWriter()
        
        # Add all pages except those to delete
        for page_num, page in enumerate(reader.pages, start=1):
            if page_num not in pages_to_delete:
                writer.add_page(page)
        
        # Write the modified PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully deleted {len(pages_to_delete)} pages from PDF")
        return True
        
    except Exception as e:
        print(f"Error deleting pages: {str(e)}")
        raise e


def extract_pages(input_file: str, output_path: str, pages_to_extract: List[int]) -> bool:
    """
    Extract specific pages from PDF into a new PDF.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the extracted pages will be saved
        pages_to_extract: List of page numbers (1-indexed) to extract
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not pages_to_extract:
            raise ValueError("Pages to extract cannot be empty")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        reader = PdfReader(input_file)
        total_pages = len(reader.pages)
        
        # Validate page numbers
        for page_num in pages_to_extract:
            if page_num < 1 or page_num > total_pages:
                raise ValueError(f"Invalid page number: {page_num}. Must be between 1 and {total_pages}")
        
        writer = PdfWriter()
        
        # Add only specified pages
        for page_num in pages_to_extract:
            writer.add_page(reader.pages[page_num - 1])
        
        # Write the extracted pages
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully extracted {len(pages_to_extract)} pages from PDF")
        return True
        
    except Exception as e:
        print(f"Error extracting pages: {str(e)}")
        raise e
