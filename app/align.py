import os
import cv2
import numpy as np


# Define regions (x1, y1, x2, y2)
regions = {
    'top_banner': (177, 142, 1092, 334),
    'sim_cards': (172, 310, 508, 735),
    'main_graphic': (523, 351, 1174, 814),
}

def align_and_crop_regions(input_image_path, output_messages, upload_folder):
    output_messages.append("Starting alignment process...")

    # Get the absolute path of the app's root directory
    app_root = os.path.dirname(os.path.abspath(__file__))

    # Load images
    template_path = os.path.join(app_root, 'template.jpg')
    template = cv2.imread(template_path)
    input_image = cv2.imread(input_image_path)

    if template is None:
        output_messages.append(f"Error loading template image from {template_path}")
        return None, None
    if input_image is None:
        output_messages.append(f"Error loading input image from {input_image_path}")
        return None, None

    # Convert to grayscale
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    gray_input = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # Detect SIFT keypoints and descriptors
    sift = cv2.SIFT_create(nfeatures=50000)
    keypoints_template, descriptors_template = sift.detectAndCompute(gray_template, None)
    keypoints_input, descriptors_input = sift.detectAndCompute(gray_input, None)

    # Use FLANN based matcher
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=500)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(descriptors_template, descriptors_input, k=2)

    # Store good matches using Lowe's ratio test
    good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

    # Extract matched points and compute homography
    if len(good_matches) > 10:
        src_pts = np.float32([keypoints_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints_input[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Compute Homography
        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

        # Warp the input image to align with the template
        height, width, channels = template.shape
        aligned_image = cv2.warpPerspective(input_image, H, (width, height))

        # Save aligned image
        output_aligned_path = os.path.join(upload_folder, 'aligned.jpg')
        cv2.imwrite(output_aligned_path, aligned_image)

        max_vals = []
        output_messages.append("Cropping regions...")

        # Crop and save each region
        for region_name, (x1, y1, x2, y2) in regions.items():
            # Crop the region from the aligned image
            aligned_crop = aligned_image[y1:y2, x1:x2]

            # Create directory for region if it doesn't exist
            region_dir = os.path.join(upload_folder, 'regions', region_name)
            if not os.path.exists(region_dir):
                os.makedirs(region_dir)

            # Save cropped region as 'input.jpg'
            cropped_image_path = os.path.join(region_dir, 'input.jpg')
            cv2.imwrite(cropped_image_path, aligned_crop)
            output_messages.append(f"Cropped and saved region '{region_name}'.")

            # Check for alignment success
            template_crop = template[y1:y2, x1:x2]

            # Convert crops to grayscale
            aligned_crop_gray = cv2.cvtColor(aligned_crop, cv2.COLOR_BGR2GRAY)
            template_crop_gray = cv2.cvtColor(template_crop, cv2.COLOR_BGR2GRAY)

            # Perform template matching
            match_result = cv2.matchTemplate(aligned_crop_gray, template_crop_gray, cv2.TM_CCOEFF_NORMED)

            # Get the match score
            _, max_val, _, _ = cv2.minMaxLoc(match_result)
            max_vals.append(max_val)

        # Check if the maximum of the max_vals is less than 0.40
        if max(max_vals) < 0.40:
            return None, None
        else:
            output_messages.append("Alignment successful.")
            # Return the homography matrix and input image dimensions
            input_image_shape = input_image.shape
            return H, input_image_shape
    else:
        return None, None
