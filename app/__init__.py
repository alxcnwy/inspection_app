from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_bootstrap import Bootstrap
from config import Config

db = SQLAlchemy()
migrate = Migrate()
images = UploadSet('images', IMAGES)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    configure_uploads(app, images)
    Bootstrap(app)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
