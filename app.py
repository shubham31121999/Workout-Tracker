from flask import Flask
from routes import init_routes
from database import db
from flask_jwt_extended import JWTManager
import secrets
def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
    app.config['SECRET_KEY'] = secrets.token_hex(32)  # For session management (flash, cookies)
    app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)

    # Initialize Extensions
    db.init_app(app)
    JWTManager(app)

    # Register Routes
    init_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()

    # Ensure database tables are created
    with app.app_context():
        db.create_all()

    app.run(debug=True)

