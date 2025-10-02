from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)

    # create instance folder if not exists (for sqlite file)
    try:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception as e:
        print("Error creando carpetas:", e)

    db.init_app(app)

    with app.app_context():
        # importar modelos para que se registren con SQLAlchemy
        from models import User, Product, Order, FinanceEntry
        db.create_all()  # crea la DB si no existe

    # registrar vistas
    from views import bp
    app.register_blueprint(bp)

    return app
