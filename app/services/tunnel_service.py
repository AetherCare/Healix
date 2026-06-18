"""
Tunnel URL reader for ngrok URL rotation handling.
"""

from pathlib import Path
from typing import Optional

from app.core.config import get_settings


def read_tunnel_url() -> Optional[str]:
    """
    Read the current public tunnel URL from the .tunnel_url file.

    Returns:
        HTTPS tunnel URL or None if file is missing/empty.
    """
    settings = get_settings()
    path = Path(settings.tunnel_url_file)
    if not path.exists():
        return None
    url = path.read_text(encoding="utf-8").strip()
    return url if url else None
