"""
Emergency card QR code generation service.
"""

import io
import json
from typing import Dict
from uuid import UUID

import qrcode

from app.services.storage import create_storage_backend


async def generate_qr_code(user_id: UUID, card_data: Dict) -> str:
    """
    Generate a QR code encoding emergency card data and store it.

    Returns:
        Storage URL for the generated QR code image.
    """
    storage = create_storage_backend()
    payload = json.dumps({
        "user_id": str(user_id),
        "blood_group": card_data.get("blood_group"),
        "allergies": card_data.get("allergies", []),
        "medications": card_data.get("medications", []),
        "type": "medivault_emergency_card",
    })

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    url = await storage.save(buffer.getvalue(), f"emergency_{user_id}.png", "qr_codes")
    return url
