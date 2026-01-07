"""File storage service for profile uploads."""

import os
import uuid
import aiofiles
import magic
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException

# Allowed file types
ALLOWED_DOCUMENT_TYPES = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/pdf': '.pdf',
}

ALLOWED_IMAGE_TYPES = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/gif': '.gif',
}

ALLOWED_TYPES = {**ALLOWED_DOCUMENT_TYPES, **ALLOWED_IMAGE_TYPES}

# Size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_PROFILE_SIZE = 50 * 1024 * 1024  # 50MB total per profile

# Base upload directory
UPLOAD_BASE_DIR = "/app/uploads/profile_files"


class FileStorageService:
    """Handles file storage for profile uploads."""

    def __init__(self, upload_dir: str = UPLOAD_BASE_DIR):
        self.upload_dir = upload_dir

    def get_profile_dir(self, profile_id: uuid.UUID) -> str:
        """Get the storage directory for a profile."""
        return os.path.join(self.upload_dir, str(profile_id))

    def ensure_profile_dir(self, profile_id: uuid.UUID) -> str:
        """Ensure the profile directory exists and return its path."""
        profile_dir = self.get_profile_dir(profile_id)
        os.makedirs(profile_dir, exist_ok=True)
        return profile_dir

    async def validate_file(self, file: UploadFile, file_type: str = "any") -> Tuple[str, str, int]:
        """
        Validate an uploaded file.

        Args:
            file: The uploaded file
            file_type: 'document', 'image', or 'any'

        Returns:
            Tuple of (mime_type, extension, file_size)

        Raises:
            HTTPException if validation fails
        """
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Reset file position
        await file.seek(0)

        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file not allowed")

        # Detect MIME type using python-magic
        mime_type = magic.from_buffer(content, mime=True)

        # Validate based on file_type
        if file_type == "document":
            allowed = ALLOWED_DOCUMENT_TYPES
        elif file_type == "image":
            allowed = ALLOWED_IMAGE_TYPES
        else:
            allowed = ALLOWED_TYPES

        if mime_type not in allowed:
            allowed_exts = list(allowed.values())
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed_exts)}"
            )

        extension = allowed[mime_type]

        return mime_type, extension, file_size

    async def save_file(
        self,
        file: UploadFile,
        profile_id: uuid.UUID,
        file_type: str = "any"
    ) -> Tuple[str, str, str, int]:
        """
        Save an uploaded file to the profile directory.

        Args:
            file: The uploaded file
            profile_id: Profile UUID
            file_type: 'document', 'image', or 'any'

        Returns:
            Tuple of (stored_filename, original_filename, mime_type, file_size)
        """
        # Validate file
        mime_type, extension, file_size = await self.validate_file(file, file_type)

        # Get original filename
        original_filename = file.filename or f"file{extension}"

        # Generate unique storage filename
        stored_filename = f"{uuid.uuid4()}{extension}"

        # Ensure directory exists
        profile_dir = self.ensure_profile_dir(profile_id)
        file_path = os.path.join(profile_dir, stored_filename)

        # Read and save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return stored_filename, original_filename, mime_type, file_size

    async def read_file(self, profile_id: uuid.UUID, stored_filename: str) -> bytes:
        """Read a file from storage."""
        profile_dir = self.get_profile_dir(profile_id)
        file_path = os.path.join(profile_dir, stored_filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()

    def delete_file(self, profile_id: uuid.UUID, stored_filename: str) -> bool:
        """Delete a file from storage."""
        profile_dir = self.get_profile_dir(profile_id)
        file_path = os.path.join(profile_dir, stored_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def delete_profile_files(self, profile_id: uuid.UUID) -> int:
        """Delete all files for a profile."""
        profile_dir = self.get_profile_dir(profile_id)
        deleted_count = 0

        if os.path.exists(profile_dir):
            for filename in os.listdir(profile_dir):
                file_path = os.path.join(profile_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1

            # Remove the directory if empty
            try:
                os.rmdir(profile_dir)
            except OSError:
                pass  # Directory not empty

        return deleted_count

    def get_profile_total_size(self, profile_id: uuid.UUID) -> int:
        """Get total size of all files for a profile."""
        profile_dir = self.get_profile_dir(profile_id)
        total_size = 0

        if os.path.exists(profile_dir):
            for filename in os.listdir(profile_dir):
                file_path = os.path.join(profile_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)

        return total_size

    def check_profile_size_limit(self, profile_id: uuid.UUID, additional_size: int) -> bool:
        """Check if adding a file would exceed the profile size limit."""
        current_size = self.get_profile_total_size(profile_id)
        return (current_size + additional_size) <= MAX_PROFILE_SIZE

    def get_file_type_category(self, mime_type: str) -> str:
        """Determine the file type category from MIME type."""
        if mime_type in ALLOWED_DOCUMENT_TYPES:
            return "document"
        elif mime_type in ALLOWED_IMAGE_TYPES:
            return "static"
        return "unknown"

    def get_token_type_for_document(self, mime_type: str) -> Optional[str]:
        """Get the appropriate token type for a document MIME type."""
        token_map = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'ms_word',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'ms_excel',
            'application/pdf': 'pdf',
        }
        return token_map.get(mime_type)


# Singleton instance
file_storage = FileStorageService()
