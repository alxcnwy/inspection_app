from flask import Blueprint, render_template, request, redirect, url_for, session, current_app

from .align import align_and_crop_regions, crop_regions
from .bedrock import train_bedrock
from .models import db, Model, ModelRegion, Run, Inspection
from . import images
import boto3
import os

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
        return redirect(url_for('main.upload_template_image', model_id=new_model.id))

    return render_template('model_create.html')


@main.route('/models/upload_template_image/<int:model_id>', methods=['GET', 'POST'])
def upload_template_image(model_id):
    model = Model.query.get(model_id)
    if not model:
        return redirect(url_for('main.model_create'))
    session['model_id'] = model_id

    if request.method == 'POST' and 'template_image' in request.files:
        filename = images.save(request.files['template_image'])  # Save only the filename
        model.template_image_filename = filename
        db.session.commit()

        return redirect(url_for('main.upload_good_images', model_id=model_id))

    return render_template('model_template_image.html', model=model)


@main.route('/models/upload_good_images/<int:model_id>', methods=['GET', 'POST'])
def upload_good_images(model_id):
    model = Model.query.get(model_id)
    if not model:
        return redirect(url_for('main.model_create'))
    session['model_id'] = model_id

    if request.method == 'POST':
        for i in range(1, 6):
            if f'good_image_{i}' in request.files:
                filename = images.save(request.files[f'good_image_{i}'])  # Store only filename
                setattr(model, f'good_image_{i}_filename', filename)
        db.session.commit()

        return redirect(url_for('main.draw_regions', model_id=model_id))

    return render_template('model_good_images.html', model=model)


@main.route('/models/upload_region_images', methods=['POST'])
def upload_region_images():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    x1 = request.form['x1']
    y1 = request.form['y1']
    x2 = request.form['x2']
    y2 = request.form['y2']
    region_name = request.form['region_name']
    fail_description = request.form['fail_description']
    pass_description = request.form['pass_description']

    bad_images = []
    for i in range(1, 6):
        if f'bad_image_{i}' in request.files:
            filename = images.save(request.files[f'bad_image_{i}'])
            bad_images.append(filename)

    new_region = ModelRegion(model_id=model_id, x1=x1, y1=y1, x2=x2, y2=y2, name=region_name)

    # Assign the saved filenames to the new region
    for i, filename in enumerate(bad_images, 1):
        setattr(new_region, f'bad_image_{i}_filename', filename)

    db.session.add(new_region)
    db.session.commit()

    # Save fail and pass descriptions for the model
    model = Model.query.get(model_id)
    model.fail_description = fail_description
    model.pass_description = pass_description
    db.session.commit()

    return redirect(url_for('main.draw_regions', model_id=model_id))


@main.route('/models/draw_regions/<int:model_id>', methods=['GET', 'POST'])
def draw_regions(model_id):
    model = Model.query.get(model_id)
    if not model:
        return redirect(url_for('main.model_create'))
    session['model_id'] = model_id

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
        'bad_image_5_url': region.bad_image_5_url,
        'fail_description': region.fail_description,
        'pass_description': region.pass_description
    }
    return region_data


@main.route('/models/finish_regions', methods=['POST'])
def finish_regions():
    model_id = session.get('model_id')
    if not model_id:
        return redirect(url_for('main.model_create'))

    model = Model.query.get(model_id)

    # Process good images and align them
    for i in range(1, 6):
        good_image_filename = getattr(model, f'good_image_{i}_filename')  # Now fetching filename
        if good_image_filename:
            good_image_path = os.path.join('app/static/uploads', good_image_filename)
            aligned_image_path = align_and_crop_regions(good_image_path, model)
            if aligned_image_path:
                setattr(model, f'good_image_{i}_aligned_filename', os.path.basename(aligned_image_path))  # Save filename
            else:
                setattr(model, f'good_image_{i}_aligned_filename', None)

    # Process bad images for each region and align them
    for region in model.regions:
        for i in range(1, 6):
            bad_image_filename = getattr(region, f'bad_image_{i}_filename')  # Now fetching filename
            if bad_image_filename:
                bad_image_path = os.path.join('app/static/uploads', bad_image_filename)
                aligned_image_path = align_and_crop_regions(bad_image_path, model)
                if aligned_image_path:
                    setattr(region, f'bad_image_{i}_aligned_filename', os.path.basename(aligned_image_path))  # Save filename
                else:
                    setattr(region, f'bad_image_{i}_aligned_filename', None)

    db.session.commit()

    return redirect(url_for('main.review_images', model_id=model.id))


@main.route('/models/<int:model_id>/review_images', methods=['GET', 'POST'])
def review_images(model_id):
    model = Model.query.get_or_404(model_id)

    # If new images were uploaded, handle alignment
    if request.method == 'POST':
        for i in range(1, 6):
            if f'good_image_{i}' in request.files:
                filename = images.save(request.files[f'good_image_{i}'])
                setattr(model, f'good_image_{i}_filename', filename)  # Save the filename instead of URL
                good_image_path = os.path.join('app/static/uploads', filename)
                aligned_image_path = align_and_crop_regions(good_image_path, model)
                if aligned_image_path:
                    setattr(model, f'good_image_{i}_aligned_filename', os.path.basename(aligned_image_path))  # Save filename
                else:
                    setattr(model, f'good_image_{i}_aligned_filename', None)

        for region in model.regions:
            for i in range(1, 6):
                if f'bad_image_{region.id}_{i}' in request.files:
                    filename = images.save(request.files[f'bad_image_{region.id}_{i}'])
                    setattr(region, f'bad_image_{i}_filename', filename)  # Save the filename instead of URL
                    bad_image_path = os.path.join('app/static/uploads', filename)
                    aligned_image_path = align_and_crop_regions(bad_image_path, model)
                    if aligned_image_path:
                        setattr(region, f'bad_image_{i}_aligned_filename', os.path.basename(aligned_image_path))  # Save filename
                    else:
                        setattr(region, f'bad_image_{i}_aligned_filename', None)

        db.session.commit()

    # Check if all images are aligned
    all_images_aligned = True
    missing_good_images = {}
    for i in range(1, 6):
        aligned_image = getattr(model, f'good_image_{i}_aligned_filename')
        if not aligned_image:
            missing_good_images[f'good_image_{i}'] = True
            all_images_aligned = False

    missing_bad_images_by_region = {}
    for region in model.regions:
        missing_bad_images = {}
        for i in range(1, 6):
            aligned_image = getattr(region, f'bad_image_{i}_aligned_filename')
            if not aligned_image:
                missing_bad_images[f'bad_image_{i}'] = True
                all_images_aligned = False
        missing_bad_images_by_region[region.name] = missing_bad_images

    if all_images_aligned:
        return render_template('model_review_images.html', all_images_aligned=True, model=model)

    return render_template('model_review_images.html', model=model, missing_good_images=missing_good_images, missing_bad_images_by_region=missing_bad_images_by_region, all_images_aligned=False)


@main.route('/models/finish/<int:model_id>', methods=['POST'])
def finish_model(model_id):
    model = Model.query.get_or_404(model_id)

    # For each region, align good and bad images, crop regions, and save URLs
    for region in model.regions:
        good_img_urls = []
        bad_img_urls = []
        output_dir = current_app.config['UPLOADED_IMAGES_DEST']

        # Align and crop good images
        for i in range(1, 6):
            good_image_filename = getattr(model, f'good_image_{i}_aligned_filename')
            if good_image_filename:
                good_image_path = os.path.join(output_dir, good_image_filename)
                cropped_good_image = crop_regions(good_image_path, model, region)
                if cropped_good_image:
                    setattr(region, f'good_image_{i}_crop', os.path.basename(cropped_good_image))
                    good_img_urls.append(cropped_good_image)

        # Align and crop bad images
        for i in range(1, 6):
            bad_image_filename = getattr(region, f'bad_image_{i}_aligned_filename')
            if bad_image_filename:
                bad_image_path = os.path.join(output_dir, bad_image_filename)
                cropped_bad_image = crop_regions(bad_image_path, model, region)
                if cropped_bad_image:
                    setattr(region, f'bad_image_{i}_crop', os.path.basename(cropped_bad_image))
                    bad_img_urls.append(cropped_bad_image)

        # Run bedrock training
        train_bedrock(good_img_urls, bad_img_urls, region)

    model.status = 'ready'
    db.session.commit()

    return redirect(url_for('main.model_list'))



@main.route('/models/<int:model_id>')
def model_detail(model_id):
    model = Model.query.get_or_404(model_id)

    # If the model is still in setup, redirect to the relevant step
    if model.status == 'setup':
        if not model.template_image_filename:
            return redirect(url_for('main.upload_template_image', model_id=model_id))
        elif not all([
            model.good_image_1_filename,
            model.good_image_2_filename,
            model.good_image_3_filename,
            model.good_image_4_filename,
            model.good_image_5_filename
        ]):
            return redirect(url_for('main.upload_good_images', model_id=model_id))
        else:
            # Check if all good images have aligned versions
            all_images_aligned = any([
                getattr(model, f'good_image_{i}_aligned_filename') for i in range(1, 6)
            ])
            if all_images_aligned:
                return redirect(url_for('main.review_images', model_id=model_id))
            else:
                return redirect(url_for('main.draw_regions', model_id=model_id))

    # Generate full image URLs/paths for template and good images
    template_image_url = model.get_image_path(model.template_image_filename)
    good_images_urls = [
        model.get_image_path(model.good_image_1_filename),
        model.get_image_path(model.good_image_2_filename),
        model.get_image_path(model.good_image_3_filename),
        model.get_image_path(model.good_image_4_filename),
        model.get_image_path(model.good_image_5_filename),
    ]

    return render_template('model_detail.html', model=model, template_image_url=template_image_url)


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
