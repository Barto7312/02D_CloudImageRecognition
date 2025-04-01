import azure.functions as func
import logging
import os
import requests
from azure.storage.blob import BlobServiceClient
import time
import json

app = func.FunctionApp()

VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")
VISION_KEY = os.getenv("VISION_KEY")
STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")

# Function to call Azure Vision API and get the caption
def analyze_image(image_url):
    headers = {
        "Ocp-Apim-Subscription-Key": VISION_KEY,
        "Content-Type": "application/json"
    }
    params = {
        "visualFeatures": "Description,Tags",  
        "language": "en"
    }
    body = {"url": image_url}

    response = requests.post(f"{VISION_ENDPOINT}/vision/v3.2/analyze", headers=headers, params=params, json=body)
    logging.info(f"Vision API response: {response.status_code} - {response.text}")
    return response.json()

#connect to blob storage
blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=STORAGE_ACCOUNT_KEY
)
container_client = blob_service_client.get_container_client("uploaded-images")

@app.route(route="upload-image", methods=["POST"])
def UploadImage(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Received image upload request")

    # Check if request contains a file
    file = req.files.get("image")
    if not file:
        return func.HttpResponse("No image file found in request", status_code=400)

    # Create unique blob name
    blob_name = f"{int(time.time())}-{file.filename}"
    
    # Upload image to Blob Storage
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.stream.read(), overwrite=True)

    # Construct the image URL from the blob storage
    image_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/uploaded-images/{blob_name}"
    logging.info(f"Image URL: {image_url}")

    # Call Azure Vision API to get the caption
    result = analyze_image(image_url)

    # Extract the caption from the result
    captions = result.get("description", {}).get("captions", [])
    if captions:
        caption = captions[0]["text"]
    else:
        caption = "No caption found"

    # Extract the tags from the result
    tags = result.get("tags", [])
    tags_list = [tag["name"] for tag in tags]  # Create a list of tag names

    logging.info(f"Image Caption: {caption}")
    logging.info(f"Image Tags: {tags_list}")

    # Prepare the response with the image caption
    response_data = {
        "message": f"Image uploaded successfully: {blob_name}",
        "caption": caption,
        "tags": tags_list
    }

    #delete the blob after processing
    delete_blob_from_storage(blob_name)

    # Return the caption and success message as JSON
    return func.HttpResponse(
        json.dumps(response_data),
        mimetype="application/json",
        status_code=200,
    )

# Delete the blob
def delete_blob_from_storage(blob_name):
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        logging.info(f"Blob {blob_name} deleted successfully.")
    except Exception as e:
        logging.error(f"Error deleting blob {blob_name}: {str(e)}")
