from datetime import datetime
from typing import Callable

from access_control import AccessAction, AccessControlManager, AccessRequest
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AccessControlMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce consent-based access control"""

    def __init__(self, app, access_control_manager: AccessControlManager):
        super().__init__(app)
        self.access_control = access_control_manager

        # Define which endpoints require access control
        self.protected_endpoints = {
            "/genes/{gene}/interpret": AccessAction.ANALYZE_VARIANTS,
            "/theories/{theory_id}/execute": AccessAction.EXECUTE_THEORY,
            "/reports/variant": AccessAction.GENERATE_REPORTS,
            "/reports/gene": AccessAction.GENERATE_REPORTS,
            "/genomic/materialize/{individual_id}/{anchor_id}": AccessAction.READ_GENOMIC_DATA,
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through access control"""

        # Check if this endpoint requires access control
        action = self._get_required_action(request.url.path, request.method)

        if action and request.method in ["POST", "GET"]:
            # Extract user ID from request (in production, this would come from JWT/session)
            user_id = self._extract_user_id(request)

            if user_id:
                # Create access request
                access_request = AccessRequest(
                    user_id=user_id,
                    action=action,
                    resource_id=request.url.path,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    ip_address=request.client.host,
                    metadata={
                        "method": request.method,
                        "user_agent": request.headers.get("user-agent", "unknown"),
                    },
                )

                # Check access
                result = self.access_control.check_access(access_request)

                if not result.granted:
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "Access denied",
                            "reason": result.reason,
                            "audit_id": result.audit_id,
                            "required_consents": [
                                ct.value for ct in result.consent_types_checked
                            ],
                        },
                    )

                # Add audit ID to response headers
                response = await call_next(request)
                response.headers["X-Access-Audit-ID"] = result.audit_id
                return response

        # No access control required or user not identified
        return await call_next(request)

    def _get_required_action(self, path: str, method: str) -> AccessAction:
        """Determine if path requires access control"""
        for endpoint_pattern, action in self.protected_endpoints.items():
            if self._path_matches(path, endpoint_pattern):
                return action
        return None

    def _path_matches(self, actual_path: str, pattern: str) -> bool:
        """Check if actual path matches pattern with variables"""
        # Simple pattern matching - in production use more sophisticated routing
        pattern_parts = pattern.split("/")
        actual_parts = actual_path.split("/")

        if len(pattern_parts) != len(actual_parts):
            return False

        for pattern_part, actual_part in zip(pattern_parts, actual_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue  # Variable part matches anything
            elif pattern_part != actual_part:
                return False

        return True

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request"""
        # In production, this would extract from JWT token or session
        # For demo purposes, check headers or query params
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            # Try query parameter
            user_id = request.query_params.get("user_id")
        return user_id
