from flask import Flask
from routes import init_routes
from database import db
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import secrets

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
    db.init_app(app)
    JWTManager(app)
    CSRFProtect(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Redirect to the 'login' route if unauthenticated

    # User loader function for Flask-Login
    from models import User  # Ensure User model is imported here

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Routes
    init_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()

    # Ensure database tables are created
    with app.app_context():
        db.create_all()

    app.run(debug=True)
