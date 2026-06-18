"""
Structural audit logging for all write operations.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

audit_logger = logging.getLogger("medivault.audit")


def log_audit_event(
    action: str,
    resource_type: str,
    user_id: Optional[UUID],
    resource_id: Optional[UUID] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Record a structured audit log entry for write operations.

    Args:
        action: Verb describing the operation (create, update, delete, etc.).
        resource_type: Entity name (User, MedicalRecord, etc.).
        user_id: Acting user UUID or None for system actions.
        resource_id: Target resource UUID when applicable.
        details: Additional context payload.
    """
    audit_logger.info(
        "audit_event",
        extra={
            "action": action,
            "resource_type": resource_type,
            "user_id": str(user_id) if user_id else None,
            "resource_id": str(resource_id) if resource_id else None,
            "details": details or {},
        },
    )
