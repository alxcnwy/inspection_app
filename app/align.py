import os
import cv2
import numpy as np
import time


def align_and_crop_regions(input_image_path, model):
    """
    Align the input image with the template image from the model, check the alignment
    by cropping regions, and return the aligned image. The aligned image is saved, but
    the cropped regions are only processed in memory and not saved.
    """
    # Get the local template image path
    template_path = model.get_template_image_path()

    if not template_path:
        raise ValueError("Template image path not found in the model.")

    template = cv2.imread(template_path)
    input_image = cv2.imread(input_image_path)

    if template is None or input_image is None:
        raise ValueError("Either template or input image could not be loaded.")

    # Convert images to grayscale
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

    # Apply Lowe's ratio test
    good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

    if len(good_matches) > 10:
        # Extract matched points
        src_pts = np.float32([keypoints_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints_input[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Compute homography
        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

        # Align the input image
        height, width, channels = template.shape
        aligned_image = cv2.warpPerspective(input_image, H, (width, height))

        # Process the regions (only in-memory, no saving)
        max_vals = []
        for region in model.regions:
            x1, y1, x2, y2 = region.x1, region.y1, region.x2, region.y2

            # Ensure coordinates are ordered correctly
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            aligned_crop = aligned_image[y1:y2, x1:x2]
            template_crop = template[y1:y2, x1:x2]

            # Check if aligned_crop is valid
            if aligned_crop is None or aligned_crop.size == 0:
                raise ValueError(f"Failed to load or process image: {input_image_path}")

            # Convert to grayscale for matching
            aligned_crop_gray = cv2.cvtColor(aligned_crop, cv2.COLOR_BGR2GRAY)
            template_crop_gray = cv2.cvtColor(template_crop, cv2.COLOR_BGR2GRAY)

            # Perform template matching
            match_result = cv2.matchTemplate(aligned_crop_gray, template_crop_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(match_result)
            max_vals.append(max_val)

        # Check if alignment was successful based on match scores
        print(input_image_path, max_vals)
        if max(max_vals) > 0:
            return None  # Alignment failed
        else:
            # Save the aligned image
            aligned_image_name = os.path.splitext(os.path.basename(input_image_path))[0] + '_aligned.jpg'
            aligned_image_path = os.path.join('app/static/uploads', aligned_image_name)
            cv2.imwrite(aligned_image_path, aligned_image)

            return aligned_image_path
    return None


def crop_regions(input_image_path, model, region):
    """
    Align the input image with the template image from the model, crop the region, save the cropped region,
    and return the path of the cropped region image with a unique timestamp to avoid overwriting.
    """
    # Get the local template image path
    template_path = model.get_template_image_path()

    if not template_path:
        raise ValueError("Template image path not found in the model.")

    template = cv2.imread(template_path)
    input_image = cv2.imread(input_image_path)

    if template is None or input_image is None:
        raise ValueError("Either template or input image could not be loaded.")

    # Convert images to grayscale
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

    # Apply Lowe's ratio test
    good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

    if len(good_matches) > 10:
        # Extract matched points
        src_pts = np.float32([keypoints_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints_input[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Compute homography
        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

        # Align the input image
        height, width, channels = template.shape
        aligned_image = cv2.warpPerspective(input_image, H, (width, height))

        # Ensure coordinates are ordered correctly for the region
        x1, x2 = min(region.x1, region.x2), max(region.x1, region.x2)
        y1, y2 = min(region.y1, region.y2), max(region.y1, region.y2)

        # Crop the region from the aligned image
        cropped_region = aligned_image[y1:y2, x1:x2]

        # Generate a unique cropped image filename with a timestamp to avoid overwrites
        timestamp = int(time.time())
        cropped_image_name = f"{os.path.splitext(os.path.basename(input_image_path))[0]}_crop_{region.id}_{timestamp}.jpg"
        cropped_image_path = os.path.join('app/static/uploads', cropped_image_name)

        # Save the cropped region
        cv2.imwrite(cropped_image_path, cropped_region)

        return cropped_image_path
    else:
        return None
