import os
from pypdf import PdfReader, PdfWriter
from typing import Optional


def protect_pdf(input_file: str, output_path: str, password: str, encryption_level: str = "AES-128", allow_print: bool = True, allow_copy: bool = True, allow_modify: bool = True) -> bool:
    """
    Protect PDF with password encryption.
    
    Args:
        input_file: Path to the input PDF file
        output_path: Path where the protected PDF will be saved
        password: Password for encryption
        encryption_level: Encryption level ('AES-128' or 'AES-256')
        allow_print: Allow printing
        allow_copy: Allow copying content
        allow_modify: Allow modification
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        reader = PdfReader(input_file)
        writer = PdfWriter()
        
        # Add all pages from original
        for page in reader.pages:
            writer.add_page(page)
        
        # Set encryption permissions
        if encryption_level == "AES-256":
            encryption = writer.encrypt(
                user_password=password,
                owner_password=None,
                use_128bit=True,
                permissions_flag=0
            )
        else:
            encryption = writer.encrypt(
                user_password=password,
                owner_password=None,
                use_128bit=False,
                permissions_flag=0
            )
        
        # Write the protected PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully protected PDF with {encryption_level} encryption")
        return True
        
    except Exception as e:
        print(f"Error protecting PDF: {str(e)}")
        raise e


def unlock_pdf(input_file: str, output_path: str, password: str) -> bool:
    """
    Remove password protection from PDF.
    
    Args:
        input_file: Path to the input protected PDF file
        output_path: Path where the unlocked PDF will be saved
        password: Password to unlock the PDF
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        if not password:
            raise ValueError("Password cannot be empty")
        
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try to read the protected PDF
        try:
            reader = PdfReader(input_file)
            if reader.is_encrypted:
                if not reader.decrypt(password):
                    raise ValueError("Incorrect password or PDF is not encrypted with this password")
        except Exception as e:
            raise ValueError(f"Failed to decrypt PDF: {str(e)}")
        
        writer = PdfWriter()
        
        # Add all pages from decrypted PDF
        for page in reader.pages:
            writer.add_page(page)
        
        # Write the unprotected PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"Successfully unlocked PDF")
        return True
        
    except Exception as e:
        print(f"Error unlocking PDF: {str(e)}")
        raise e
