import os

import boto3
import json
import base64
import time
import pickle
from datetime import datetime
import requests
from flask import current_app


def encode_image_to_base64_from_disk(image_path):
    # Open and encode image to base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



def send_request(model_id, new_message, conversation_history, save=False, region=None):
    start_time_request = time.time()
    print(f"{datetime.now()} Request Start")

    bedrock = boto3.client('bedrock-runtime')

    # Append the new message to conversation history
    conversation_history.append({
        "role": "user",
        "content": new_message
    })

    # Prepare the request body
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2000,
        "messages": conversation_history
    }

    # Convert the body to JSON and encode as bytes
    body_json = json.dumps(body).encode('utf-8')

    # Make the request to Bedrock
    response = bedrock.invoke_model(
        modelId=model_id,
        body=body_json,
        contentType="application/json",
        accept="application/json"
    )

    # Read the response body
    response_body = response['body'].read()

    # Parse the response
    assistant_response = json.loads(response_body)

    # Append the assistant's response to the conversation history
    conversation_history.append({
        "role": "assistant",
        "content": assistant_response["content"]
    })

    # Save the conversation history if needed
    if save and region:
        filename = f"{region.id}.pkl"
        save_path = os.path.join(current_app.config['UPLOADED_IMAGES_DEST'], filename)
        with open(save_path, 'wb') as f:
            pickle.dump(conversation_history, f)

    # Print total request time
    end_time_request = time.time()
    total_time = end_time_request - start_time_request
    print(f"{datetime.now()} Request End: {total_time:.2f} seconds")

    return assistant_response


def train_bedrock(good_img_urls, bad_img_urls, region):
    # Initialize conversation history
    conversation_history = []
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    # Process fail images
    fail_images_content = []
    for image_path in bad_img_urls:
        encoded_image = encode_image_to_base64_from_disk(image_path)  # Fetch from disk
        fail_images_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encoded_image
            }
        })

    # Add fail image description
    fail_images_content.append({
        "type": "text",
        "text": f"Your job is to examine examples of incorrect and correct images and learn how to tell if a new image is incorrect or correct. Here are 5 'incorrect' images. {region.fail_description} Provide descriptions for these images and end each description with the word 'incorrect'."
    })

    # Send fail images to Bedrock
    fail_response = send_request(model_id, fail_images_content, conversation_history)
    print(f"{datetime.now()} Response for 5 fail images:")
    print(fail_response)

    # Process pass images
    pass_images_content = []
    for image_path in good_img_urls:
        encoded_image = encode_image_to_base64_from_disk(image_path)  # Fetch from disk
        pass_images_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": encoded_image
            }
        })

    # Add pass image description
    pass_images_content.append({
        "type": "text",
        "text": f"Here are 5 'correct' images. {region.pass_description} Provide descriptions for these images and end each description with the word 'correct'."
    })

    # Send pass images to Bedrock
    pass_response = send_request(model_id, pass_images_content, conversation_history, save=True, region=region)
    print(f"{datetime.now()} Response for 5 pass images:")
    print(pass_response)

