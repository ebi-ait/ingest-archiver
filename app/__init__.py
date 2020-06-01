import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Construct the core application."""
    app = Flask(__name__)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(project_dir, "archiver.db")
    database_file = f"sqlite:///{db_path}"
    db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI', database_file)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri

    db.init_app(app)

    with app.app_context():
        from . import routes  # Import routes
        db.create_all()  # Create database tables for our data models

        return app
