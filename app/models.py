from . import db
from datetime import datetime


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    template_image_url = db.Column(db.String(256))
    good_image_1_url = db.Column(db.String(256))
    good_image_2_url = db.Column(db.String(256))
    good_image_3_url = db.Column(db.String(256))
    good_image_4_url = db.Column(db.String(256))
    good_image_5_url = db.Column(db.String(256))
    status = db.Column(db.String(64), default='setup')  # 'setup', 'ready', 'running'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    regions = db.relationship('ModelRegion', backref='model', lazy=True)
    runs = db.relationship('Run', backref='model', lazy=True)




class ModelRegion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    name = db.Column(db.String(256))
    x1 = db.Column(db.Integer, nullable=False)
    y1 = db.Column(db.Integer, nullable=False)
    x2 = db.Column(db.Integer, nullable=False)
    y2 = db.Column(db.Integer, nullable=False)
    bad_image_1_url = db.Column(db.String(256))
    bad_image_2_url = db.Column(db.String(256))
    bad_image_3_url = db.Column(db.String(256))
    bad_image_4_url = db.Column(db.String(256))
    bad_image_5_url = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    s3_path = db.Column(db.String(256))
    result = db.Column(db.String(64))  # "55/60 PASS"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Inspections
    inspections = db.relationship('Inspection', backref='run', lazy=True)


class Inspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=False)
    image_url = db.Column(db.String(256))
    pass_fail = db.Column(db.Boolean, default=False)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
