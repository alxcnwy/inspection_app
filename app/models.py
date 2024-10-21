from . import db
from datetime import datetime
import os
from flask import current_app


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    template_image_filename = db.Column(db.String(256))  # Changed to store only filename

    good_image_1_filename = db.Column(db.String(256))
    good_image_2_filename = db.Column(db.String(256))
    good_image_3_filename = db.Column(db.String(256))
    good_image_4_filename = db.Column(db.String(256))
    good_image_5_filename = db.Column(db.String(256))

    # Aligned image paths
    good_image_1_aligned_filename = db.Column(db.String(256))
    good_image_2_aligned_filename = db.Column(db.String(256))
    good_image_3_aligned_filename = db.Column(db.String(256))
    good_image_4_aligned_filename = db.Column(db.String(256))
    good_image_5_aligned_filename = db.Column(db.String(256))

    status = db.Column(db.String(64), default='setup')  # 'setup', 'ready', 'running'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    regions = db.relationship('ModelRegion', backref='model', lazy=True)
    runs = db.relationship('Run', backref='model', lazy=True)

    def get_image_path(self, image_filename):
        """Get the full local path for an image."""
        if image_filename:
            return os.path.join(current_app.config['UPLOADED_IMAGES_DEST'], image_filename)
        return None

    def get_template_image_path(self):
        """Return the full path to the template image."""
        return self.get_image_path(self.template_image_filename)


class ModelRegion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    name = db.Column(db.String(256))

    model_pkl = db.Column(db.String(256), nullable=True)

    fail_description = db.Column(db.Text, nullable=True)  # Added
    pass_description = db.Column(db.Text, nullable=True)  # Added

    x1 = db.Column(db.Integer, nullable=False)
    y1 = db.Column(db.Integer, nullable=False)
    x2 = db.Column(db.Integer, nullable=False)
    y2 = db.Column(db.Integer, nullable=False)

    # Store filenames instead of URLs for bad images
    bad_image_1_filename = db.Column(db.String(256))
    bad_image_2_filename = db.Column(db.String(256))
    bad_image_3_filename = db.Column(db.String(256))
    bad_image_4_filename = db.Column(db.String(256))
    bad_image_5_filename = db.Column(db.String(256))

    # Store filenames instead of URLs for aligned bad images
    bad_image_1_aligned_filename = db.Column(db.String(256))
    bad_image_2_aligned_filename = db.Column(db.String(256))
    bad_image_3_aligned_filename = db.Column(db.String(256))
    bad_image_4_aligned_filename = db.Column(db.String(256))
    bad_image_5_aligned_filename = db.Column(db.String(256))

    # Store filenames for cropped bad images
    bad_image_1_crop = db.Column(db.String(256))
    bad_image_2_crop = db.Column(db.String(256))
    bad_image_3_crop = db.Column(db.String(256))
    bad_image_4_crop = db.Column(db.String(256))
    bad_image_5_crop = db.Column(db.String(256))

    # Store filenames for cropped good images
    good_image_1_crop = db.Column(db.String(256))
    good_image_2_crop = db.Column(db.String(256))
    good_image_3_crop = db.Column(db.String(256))
    good_image_4_crop = db.Column(db.String(256))
    good_image_5_crop = db.Column(db.String(256))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def get_bad_image_path(self, image_filename):
        """Get the full local path for a bad image."""
        if image_filename:
            return os.path.join(current_app.config['UPLOADED_IMAGES_DEST'], image_filename)
        return None


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
    run_id = db.Column(db.Integer, db.ForeignKey('run.id'), nullable=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)  # New field to store the model
    image_url = db.Column(db.String(256))
    pass_fail = db.Column(db.Boolean, default=False)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Establish a relationship with the Model
    model = db.relationship('Model', backref='inspections', lazy=True)
