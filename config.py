import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:supersecretpassword@localhost:3306/inspection'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOADED_IMAGES_DEST = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    S3_BUCKET = os.environ.get('S3_BUCKET')
