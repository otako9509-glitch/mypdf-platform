import os
from PIL import Image
from typing import List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io


def jpg_to_pdf(image_files: List[str], output_path: str, orientation: str = "auto", margin: str = "small") -> bool:
    """
    Convert JPG images to PDF.
    
    Args:
        image_files: List of paths to JPG files
        output_path: Path where the PDF will be saved
        orientation: Page orientation ('auto', 'portrait', 'landscape')
        margin: Page margin ('none', 'small', 'large')
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not image_files:
            raise ValueError("No image files provided")
        
        for image_file in image_files:
            if not os.path.exists(image_file):
                raise FileNotFoundError(f"Image file not found: {image_file}")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Set page size based on orientation
        if orientation == "landscape":
            page_size = (A4[1], A4[0])  # Swap for landscape
        else:
            page_size = A4
        
        # Set margin
        margin_map = {
            'none': 0,
            'small': 36,  # 0.5 inch
            'large': 72   # 1 inch
        }
        margin_size = margin_map.get(margin, 36)
        
        # Create PDF
        c = canvas.Canvas(output_path, pagesize=page_size)
        
        for image_file in image_files:
            try:
                # Open image
                img = Image.open(image_file)
                img_width, img_height = img.size
                
                # Calculate available space
                available_width = page_size[0] - (2 * margin_size)
                available_height = page_size[1] - (2 * margin_size)
                
                # Calculate scaling to fit within available space
                width_ratio = available_width / img_width
                height_ratio = available_height / img_height
                scale = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = img_width * scale
                new_height = img_height * scale
                
                # Calculate position to center the image
                x = (page_size[0] - new_width) / 2
                y = (page_size[1] - new_height) / 2
                
                # Draw image
                c.drawImage(image_file, x, y, new_width, new_height)
                
                # Add new page for next image
                c.showPage()
                
                print(f"Added {os.path.basename(image_file)} to PDF")
                
            except Exception as e:
                print(f"Error processing image {image_file}: {str(e)}")
                continue
        
        # Save PDF
        c.save()
        print(f"Successfully created PDF with {len(image_files)} images")
        return True
        
    except Exception as e:
        print(f"Error converting JPG to PDF: {str(e)}")
        raise e


def images_to_pdf_directory(image_dir: str, output_path: str, orientation: str = "auto", margin: str = "small") -> bool:
    """
    Convert all JPG images in a directory to PDF.
    
    Args:
        image_dir: Directory containing JPG files
        output_path: Path where the PDF will be saved
        orientation: Page orientation ('auto', 'portrait', 'landscape')
        margin: Page margin ('none', 'small', 'large')
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(image_dir):
            raise FileNotFoundError(f"Image directory not found: {image_dir}")
        
        # Get all JPG files
        image_files = []
        for filename in sorted(os.listdir(image_dir)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(image_dir, filename))
        
        if not image_files:
            raise ValueError("No image files found in directory")
        
        return jpg_to_pdf(image_files, output_path, orientation, margin)
        
    except Exception as e:
        print(f"Error converting images directory to PDF: {str(e)}")
        raise e
