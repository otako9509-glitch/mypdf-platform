import os
import uuid
from typing import Optional
from fastapi import UploadFile


class StorageService:
    def __init__(
        self,
        uploads_path: str = "C:\\Users\\ADIL\\Documents\\pj\\storage\\uploads",
        outputs_path: str = "C:\\Users\\ADIL\\Documents\\pj\\storage\\outputs"
    ):
        self.uploads_path = uploads_path
        self.outputs_path = outputs_path
        os.makedirs(uploads_path, exist_ok=True)
        os.makedirs(outputs_path, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        # Remove path separators and special characters
        sanitized = filename.replace('\\', '').replace('/', '').replace('..', '')
        # Keep only safe characters
        safe_chars = []
        for char in sanitized:
            if char.isalnum() or char in '._- ':
                safe_chars.append(char)
        return ''.join(safe_chars) or 'file'

    def save_upload_file(
        self,
        upload_file: UploadFile,
        job_id: str
    ) -> dict:
        """
        Save an uploaded file to the uploads directory.
        Returns a dict with original_name and stored_name.
        """
        original_name = upload_file.filename or "unknown.pdf"
        sanitized_name = self._sanitize_filename(original_name)
        
        # Generate unique stored filename
        file_extension = '.pdf' if not original_name.lower().endswith('.pdf') else ''
        stored_name = f"{job_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = os.path.join(self.uploads_path, stored_name)
        
        try:
            with open(file_path, 'wb') as f:
                content = upload_file.file.read()
                f.write(content)
            
            return {
                "original_name": original_name,
                "stored_name": stored_name,
                "file_path": file_path,
                "size": len(content)
            }
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e

    def get_upload_file_path(self, stored_name: str) -> Optional[str]:
        """Get the full path of an uploaded file."""
        file_path = os.path.join(self.uploads_path, stored_name)
        if os.path.exists(file_path):
            return file_path
        return None

    def save_output_file(
        self,
        job_id: str,
        content: bytes,
        extension: str = '.pdf'
    ) -> str:
        """
        Save processed output file.
        Returns the stored filename.
        """
        stored_name = f"{job_id}_output{extension}"
        file_path = os.path.join(self.outputs_path, stored_name)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return stored_name

    def get_output_file_path(self, stored_name: str) -> Optional[str]:
        """Get the full path of an output file."""
        file_path = os.path.join(self.outputs_path, stored_name)
        if os.path.exists(file_path):
            return file_path
        return None

    def delete_file(self, file_path: str) -> bool:
        """Delete a file if it exists."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass
        return False

    def validate_pdf_magic_bytes(self, file_content: bytes) -> bool:
        """Validate that file content starts with PDF magic bytes."""
        pdf_magic = b'%PDF'
        return file_content.startswith(pdf_magic)


# Global singleton instance
storage_service = StorageService()
