import os
from flask import Flask, render_template, send_from_directory
from backend.config import Config
from database.db import db
from database.seed_data import seed_database
from backend.routes import health_bp, auth_bp, complaint_bp, provider_bp, admin_bp

def create_app(config_class=Config):
    # Set templates and static paths
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path="/static"
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints with clean API prefixes
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(complaint_bp, url_prefix="/api/complaints")
    app.register_blueprint(provider_bp, url_prefix="/api/providers")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Serve Single Page Application
    @app.route("/")
    def index():
        return render_template("index.html")

    # Initialize database tables and seed demo records
    with app.app_context():
        db.create_all()
        try:
            seed_database()
        except Exception as e:
            print(f"Notice on seed: {e}")

    return app
