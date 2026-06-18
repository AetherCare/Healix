"""
File validation: MIME-type allowlisting and maximum size enforcement.
"""

import hashlib
import mimetypes
from typing import Set, Tuple

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

ALLOWED_MIME_TYPES: Set[str] = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
    "audio/mpeg",
    "audio/wav",
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/x-wav",
    "text/plain",
}


async def validate_upload(file: UploadFile) -> Tuple[bytes, str, str]:
    """
    Validate and read an uploaded file.

    Returns:
        Tuple of (file_bytes, mime_type, sha256_hash).

    Raises:
        HTTPException: On size or MIME type violations.
    """
    settings = get_settings()
    content = await file.read()
    await file.seek(0)

    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.storage_max_file_size_mb} MB",
        )

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"MIME type '{mime_type}' is not allowed",
        )

    file_hash = hashlib.sha256(content).hexdigest()
    return content, mime_type, file_hash
