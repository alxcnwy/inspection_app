# Flask Inspection Model App

This Flask app is designed to create, manage, and run inspection models. The application includes multi-step processes for uploading images, selecting regions on a template image, and testing inspection models using images from an S3 bucket.

## Features

- **Multi-step Model Creation:**
  - Upload a template image
  - Upload 5 good images
  - Draw regions on the template image
  - Upload 5 bad images for each region
- **Run Inspections:** Run models on S3 images and get pass/fail results.
- **Model Status Tracking:** Track model statuses as `setup`, `ready`, or `running`.
- **Mocked Inspection Logic:** The app includes a placeholder inspection logic that returns "pass" for every image.

## Installation

### Requirements

- Python 3.8+
- MySQL or another SQLAlchemy-supported database
- AWS S3 (for actual image handling, though it's mocked in this app)

### Setup Instructions

1. **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd inspection_model_app
    ```

2. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure MySQL Database:**
   - Create a MySQL database (e.g., `inspection_model_db`):
     ```sql
     CREATE DATABASE inspection_model_db;
     ```
   - Update the `config.py` file with your MySQL database credentials:
     ```python
     SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/inspection_model_db'
     ```

4. **Initialize and Migrate Database:**
    ```bash
    flask db init
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

5. **Run the Application:**
    ```bash
    flask run
    ```

6. **Access the App:**
   Open your browser and visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## How to Use

### Creating a Model

1. **Create a new model:**
   - Go to the "Models" page and click "Create New Model."
   - Enter the model name and description.
   
2. **Upload Template Image:**
   - After creating the model, upload a template image.
   - A preview of the image will be displayed.

3. **Upload Good Images:**
   - Upload 5 good images, each with a preview.
   
4. **Draw Regions:**
   - Click on the template image to select regions for inspection.
   - For each region, upload 5 bad images.

5. **Finish Regions:**
   - Once the regions and bad images are uploaded, click "Finish Regions" to mark the model as `ready`.

### Running a Model

1. **Run the Model:**
   - If the model is `ready`, click "Run" to run it on S3 images (mocked in this app).
   - The inspection results (pass/fail) will be displayed.

### Model Status

- **Setup:** The model is still in the setup process.
- **Ready:** The model is ready to be run on images.
- **Running:** The model is currently being run on images.

## Mocked Inspection

The `run_inspection` function is currently mocked to return "pass" for every image. You can modify this function in `routes.py` to implement your own inspection logic.

## Additional Notes

- **AWS S3 Integration:** While AWS S3 is mentioned for handling images, the current implementation mocks the image processing. To use S3, you'll need to configure actual S3 bucket handling.
- **MySQL Configuration:** You can use other databases supported by SQLAlchemy by updating the `SQLALCHEMY_DATABASE_URI` in `config.py`.

## License

This project is licensed under the MIT License.
