import os
from pypdf import PdfReader, PdfWriter


def compress_pdf(input_file: str, output_path: str, quality: str = "medium") -> bool:
    """
    Compress a PDF file by removing redundant objects and optimizing streams.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the compressed PDF will be saved
        quality: Compression quality level ("low", "medium", "high")
    
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
        
        # Clone pages to writer (this removes redundant objects)
        for page in reader.pages:
            writer.add_page(page)
        
        # Set compression flags based on quality
        if quality == "low":
            # Minimal compression, preserve quality
            pass
        elif quality == "medium":
            # Moderate compression
            writer.remove_images()
        elif quality == "high":
            # Aggressive compression
            writer.remove_images()
            writer.remove_text()
        else:
            raise ValueError(f"Invalid quality level: {quality}")
        
        # Write the compressed PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        # Calculate compression ratio
        original_size = os.path.getsize(input_file)
        compressed_size = os.path.getsize(output_path)
        ratio = (1 - (compressed_size / original_size)) * 100
        
        print(f"Compression complete. Original: {original_size} bytes, "
              f"Compressed: {compressed_size} bytes, Reduction: {ratio:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"Error compressing PDF: {str(e)}")
        raise e


def optimize_pdf_streams(input_file: str, output_path: str) -> bool:
    """
    Optimize PDF streams by removing unused objects and compressing content streams.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the optimized PDF will be saved
    
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
        
        # Add pages and remove redundant objects
        for page in reader.pages:
            writer.add_page(page)
        
        # Remove unused objects
        writer.remove_unused_objects()
        
        # Write the optimized PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"PDF optimization complete: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error optimizing PDF: {str(e)}")
        raise e
