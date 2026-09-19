from .health_routes import health_bp
from .auth_routes import auth_bp
from .complaint_routes import complaint_bp
from .provider_routes import provider_bp
from .admin_routes import admin_bp

__all__ = ["health_bp", "auth_bp", "complaint_bp", "provider_bp", "admin_bp"]
