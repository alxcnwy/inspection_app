from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import db, Model, ModelRegion, Run, Inspection
from . import images
import boto3

main = Blueprint('main', __name__)

# AWS S3 client initialization
s3_client = boto3.client('s3')


def run_inspection(image):
    """Mock function to return 'pass' for every image."""
    pass_fail = True  # Simulated "pass" result
    reason = "All regions passed"
    return pass_fail, reason


@main.route('/')
@main.route('/models')
def model_list():
    models = Model.query.all()

    # Prepare model data including last run information
    model_data = []
    for model in models:
        last_run = Run.query.filter_by(model_id=model.id).order_by(Run.created_at.desc()).first()
        if last_run:
            model_data.append({
                'model': model,
                'last_run': last_run.created_at,
                'last_run_result': last_run.result
            })
        else:
            model_data.append({
                'model': model,
                'last_run': None,
                'last_run_result': None
            })

    return render_template('model_list.html', model_data=model_data)



@main.route('/models/new', methods=['GET', 'POST'])
def model_create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        new_model = Model(name=name, description=description)
        db.session.add(new_model)
        db.session.commit()

        session['model_id'] = new_model.id
        return redirect(url_for('main.upload_template_image'))

    return render_template('model_create.html')


@main.route('/models/upload_template_image', methods=['GET', 'POST'])
def upload_template_image():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    if request.method == 'POST' and 'template_image' in request.files:
        filename = images.save(request.files['template_image'])
        file_url = images.url(filename)
        model = Model.query.get(model_id)
        model.template_image_url = file_url
        db.session.commit()

        return redirect(url_for('main.upload_good_images'))

    return render_template('model_template_image.html')


@main.route('/models/upload_good_images', methods=['GET', 'POST'])
def upload_good_images():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    if request.method == 'POST':
        for i in range(1, 6):
            if f'good_image_{i}' in request.files:
                filename = images.save(request.files[f'good_image_{i}'])
                file_url = images.url(filename)
                model = Model.query.get(model_id)
                setattr(model, f'good_image_{i}_url', file_url)
        db.session.commit()

        return redirect(url_for('main.draw_regions'))

    return render_template('model_good_images.html')


@main.route('/models/upload_region_images', methods=['POST'])
def upload_region_images():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    x1 = request.form['x1']
    y1 = request.form['y1']
    x2 = request.form['x2']
    y2 = request.form['y2']
    region_name = request.form['region_name']  # Get the region name

    bad_images = []
    for i in range(1, 6):
        if f'bad_image_{i}' in request.files:
            filename = images.save(request.files[f'bad_image_{i}'])
            file_url = images.url(filename)
            bad_images.append(file_url)

    # Create new region with name
    new_region = ModelRegion(model_id=model_id, x1=x1, y1=y1, x2=x2, y2=y2, name=region_name)
    for i, img_url in enumerate(bad_images, 1):
        setattr(new_region, f'bad_image_{i}_url', img_url)
    db.session.add(new_region)
    db.session.commit()

    return redirect(url_for('main.draw_regions'))


@main.route('/models/draw_regions', methods=['GET', 'POST'])
def draw_regions():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    model = Model.query.get(model_id)
    return render_template('model_regions.html', model=model)


@main.route('/regions/<int:region_id>/data', methods=['GET'])
def get_region_data(region_id):
    region = ModelRegion.query.get_or_404(region_id)
    region_data = {
        'name': region.name,
        'x1': region.x1,
        'y1': region.y1,
        'x2': region.x2,
        'y2': region.y2,
        'bad_image_1_url': region.bad_image_1_url,
        'bad_image_2_url': region.bad_image_2_url,
        'bad_image_3_url': region.bad_image_3_url,
        'bad_image_4_url': region.bad_image_4_url,
        'bad_image_5_url': region.bad_image_5_url
    }
    return region_data



@main.route('/models/finish_regions', methods=['GET', 'POST'])
def finish_regions():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    model = Model.query.get(model_id)
    model.status = 'ready'
    db.session.commit()

    session.pop('model_id', None)
    return redirect(url_for('main.model_detail', model_id=model_id))


@main.route('/models/<int:model_id>')
def model_detail(model_id):
    model = Model.query.get_or_404(model_id)

    # If the model is still being set up, determine which step to send the user to
    if model.status == 'setup':
        if not model.template_image_url:
            return redirect(url_for('main.upload_template_image', model_id=model_id))
        elif not all([model.good_image_1_url, model.good_image_2_url, model.good_image_3_url, model.good_image_4_url, model.good_image_5_url]):
            return redirect(url_for('main.upload_good_images', model_id=model_id))
        else:
            return redirect(url_for('main.draw_regions', model_id=model_id))

    # If the model is ready or running, show the model detail page
    return render_template('model_detail.html', model=model)


@main.route('/models/<int:model_id>/delete', methods=['POST'])
def delete_model(model_id):
    model = Model.query.get_or_404(model_id)

    # Remove all related regions for this model
    ModelRegion.query.filter_by(model_id=model_id).delete()

    # Delete the model
    db.session.delete(model)
    db.session.commit()

    return redirect(url_for('main.model_list'))


@main.route('/models/<int:model_id>/run', methods=['POST'])
def run_model(model_id):
    model = Model.query.get_or_404(model_id)
    model.status = 'running'
    db.session.commit()

    s3_path = request.form['s3_path']
    new_run = Run(model_id=model.id, s3_path=s3_path)
    db.session.add(new_run)
    db.session.commit()

    # Simulate S3 image processing
    for i in range(10):  # Mock 10 images for the run
        image_url = f"https://mocked-s3-url.com/image_{i}.jpg"
        pass_fail, reason = run_inspection(image_url)
        inspection = Inspection(run_id=new_run.id, image_url=image_url, pass_fail=pass_fail, reason=reason)
        db.session.add(inspection)

    db.session.commit()

    model.status = 'ready'
    db.session.commit()

    return redirect(url_for('main.run_detail', run_id=new_run.id))


@main.route('/runs/<int:run_id>')
def run_detail(run_id):
    run = Run.query.get_or_404(run_id)
    inspections = Inspection.query.filter_by(run_id=run_id).all()
    return render_template('run_detail.html', run=run, inspections=inspections)


@main.route('/runs')
def run_list():
    runs = Run.query.all()
    return render_template('run_list.html', runs=runs)
