import os
from pdf2image import convert_from_path
from PIL import Image
from typing import List
import zipfile


def pdf_to_jpg(input_file: str, output_dir: str, quality: str = "medium", dpi: int = 150) -> str:
    """
    Convert PDF pages to JPG images.
    
    Args:
        input_file: Path to the input PDF file
        output_dir: Directory where images will be saved
        quality: Image quality ('low', 'medium', 'high')
        dpi: Resolution in DPI
    
    Returns:
        Path to ZIP file containing all images (if multiple pages) or single image path
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Set quality parameters
        quality_map = {
            'low': {'dpi': 72, 'quality': 75},
            'medium': {'dpi': 150, 'quality': 85},
            'high': {'dpi': 300, 'quality': 95}
        }
        
        params = quality_map.get(quality, quality_map['medium'])
        if dpi != 150:
            params['dpi'] = dpi
        
        # Convert PDF to images
        images = convert_from_path(
            input_file,
            dpi=params['dpi'],
            fmt='jpeg'
        )
        
        image_paths = []
        
        # Save each page as JPG
        for i, image in enumerate(images, start=1):
            image_path = os.path.join(output_dir, f"page_{i}.jpg")
            image.save(image_path, 'JPEG', quality=params['quality'])
            image_paths.append(image_path)
            print(f"Saved page {i} as {image_path}")
        
        # If multiple pages, create a ZIP file
        if len(image_paths) > 1:
            zip_path = os.path.join(output_dir, "images.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for image_path in image_paths:
                    zipf.write(image_path, os.path.basename(image_path))
            
            # Clean up individual images
            for image_path in image_paths:
                os.remove(image_path)
            
            print(f"Created ZIP file with {len(image_paths)} images")
            return zip_path
        else:
            print(f"Converted single page to JPG")
            return image_paths[0] if image_paths else None
        
    except Exception as e:
        print(f"Error converting PDF to JPG: {str(e)}")
        raise e


def pdf_to_single_jpg(input_file: str, output_path: str, page_number: int = 1, dpi: int = 150) -> bool:
    """
    Convert a single PDF page to JPG.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the JPG will be saved
        page_number: Page number to convert (1-indexed)
        dpi: Resolution in DPI
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert specific page
        images = convert_from_path(
            input_file,
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
            fmt='jpeg'
        )
        
        if images:
            images[0].save(output_path, 'JPEG', quality=85)
            print(f"Converted page {page_number} to {output_path}")
            return True
        else:
            raise ValueError(f"Page {page_number} not found in PDF")
        
    except Exception as e:
        print(f"Error converting PDF page to JPG: {str(e)}")
        raise e
