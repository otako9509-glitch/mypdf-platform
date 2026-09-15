import os
from pypdf import PdfReader, PdfWriter


def rotate_pdf(input_file: str, output_path: str, rotation: int = 90) -> bool:
    """
    Rotate PDF pages by specified degrees.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the rotated PDF will be saved
        rotation: Rotation angle in degrees (90, 180, or 270)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if rotation not in [90, 180, 270]:
            raise ValueError("Rotation must be 90, 180, or 270 degrees")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        reader = PdfReader(input_file)
        writer = PdfWriter()
        
        # Rotate all pages
        for page in reader.pages:
            page.rotate(rotation)
            writer.add_page(page)
        
        # Write the rotated PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully rotated PDF by {rotation} degrees")
        return True
        
    except Exception as e:
        print(f"Error rotating PDF: {str(e)}")
        raise e


def rotate_specific_pages(input_file: str, output_path: str, page_rotations: dict) -> bool:
    """
    Rotate specific pages by different angles.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the rotated PDF will be saved
        page_rotations: Dictionary mapping page numbers (1-indexed) to rotation angles
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        reader = PdfReader(input_file)
        writer = PdfWriter()
        
        # Rotate specific pages
        for page_num, page in enumerate(reader.pages, start=1):
            if page_num in page_rotations:
                rotation = page_rotations[page_num]
                if rotation in [90, 180, 270]:
                    page.rotate(rotation)
            writer.add_page(page)
        
        # Write the rotated PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully rotated specific pages in PDF")
        return True
        
    except Exception as e:
        print(f"Error rotating specific pages: {str(e)}")
        raise e
