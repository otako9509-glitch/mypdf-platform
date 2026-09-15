import os
from typing import List, Optional
from pypdf import PdfReader, PdfWriter


def split_pdf(
    input_file: str,
    output_dir: str,
    split_ranges: Optional[List[tuple]] = None
) -> List[str]:
    """
    Split a PDF file into multiple PDFs.
    
    Args:
        input_file: Path to the input PDF file
        output_dir: Directory where split PDFs will be saved
        split_ranges: List of (start_page, end_page) tuples (0-indexed).
                     If None, splits each page into a separate file.
    
    Returns:
        List of paths to the created split PDF files
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        reader = PdfReader(input_file)
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            raise ValueError("Input PDF has no pages")
        
        output_files = []
        
        if split_ranges is None:
            # Split each page into a separate file
            for page_num in range(total_pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                
                output_path = os.path.join(output_dir, f"page_{page_num + 1}.pdf")
                with open(output_path, 'wb') as f:
                    writer.write(f)
                
                output_files.append(output_path)
                print(f"Created: {output_path}")
        else:
            # Split according to provided ranges
            for idx, (start, end) in enumerate(split_ranges):
                if start < 0 or end >= total_pages or start > end:
                    raise ValueError(f"Invalid page range: {start}-{end}")
                
                writer = PdfWriter()
                for page_num in range(start, end + 1):
                    writer.add_page(reader.pages[page_num])
                
                output_path = os.path.join(output_dir, f"split_{idx + 1}_pages_{start + 1}-{end + 1}.pdf")
                with open(output_path, 'wb') as f:
                    writer.write(f)
                
                output_files.append(output_path)
                print(f"Created: {output_path}")
        
        print(f"Successfully split PDF into {len(output_files)} files")
        return output_files
        
    except Exception as e:
        print(f"Error splitting PDF: {str(e)}")
        raise e


def split_all_pages(input_file: str, output_dir: str) -> List[str]:
    """
    Split a PDF file, creating a separate file for each page.
    
    Args:
        input_file: Path to the input PDF file
        output_dir: Directory where split PDFs will be saved
    
    Returns:
        List of paths to the created split PDF files
    """
    return split_pdf(input_file, output_dir, split_ranges=None)
