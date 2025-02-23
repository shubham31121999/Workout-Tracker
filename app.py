from flask import Flask
from routes import init_routes
from database import db
from flask_jwt_extended import JWTManager
import secrets
from flask_wtf.csrf import CSRFProtect

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///workout.db"
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    app.config["JWT_SECRET_KEY"] = secrets.token_hex(32)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True  # CSRF for JWT cookies
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False  # Avoid conflicts with Flask-WTF

    # Initialize Extensions
    db.init_app(app)  # ✅ Fix: Correctly initialize the database
    JWTManager(app)
    CSRFProtect(app)

    # Register Routes
    init_routes(app)  # ✅ Fix: Proper indentation

    return app

if __name__ == "__main__":
    app = create_app()

    # Ensure database tables are created
    with app.app_context():
        db.create_all()

    app.run(debug=True)
