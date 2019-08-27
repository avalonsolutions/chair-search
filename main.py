import base64
import os
from datetime import datetime
import random

from flask import Flask, render_template, request, redirect, jsonify
from google.cloud import storage

from vision.product_catalogue import get_similar_products
from util import predict_json, crop_and_resize
from config import config as cfg

if not os.getenv("RUNNING_ON_GCP"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cfg.LOCAL_CREDENTIALS

app = Flask(__name__, static_folder='assets')

storage_client = storage.Client(project=cfg.PROJECT_ID)


@app.route("/index.html")
@app.route("/")
def root():
    return render_template("index.html")


@app.route('/autoDraw')
def auto_draw():
    files = os.listdir("assets/static_chairs")
    file = files[random.randint(0, len(files) - 1)]
    path = f"assets/static_chairs/{file}"
    resp = {
        "success": True,
        "filepath": path
    }
    return jsonify(resp)


@app.route("/generate", methods=["POST"])
def generate():
    sketch = request.json["imgBase64"]

    # resp = {
    #     "success": True,
    #     "results": [{"name": "nisse", "src": "blablabla"}, {'name': "untz", 'src': "atatata"}],
    #     "original_sketch": "ananananana",
    #     "generated_chair": "generated_chair"
    # }

    # return jsonify(resp)

    # This code below saves the drawn chair locally
    # with open("demo-chair_3.txt", 'w') as file:
    #     import json
    #     request.json.pop('imgBase64')
    #     file.write(json.dumps(request.json))

    cropped_sketch = crop_and_resize(sketch)
    model_input = {'image_bytes': {'b64': cropped_sketch}}
    generated_chair = predict_json(project="chair-search-demo", model="chair_generation", input=model_input, version=cfg.MODEL_VERSION)

    # Get similar products and filter to top 3
    similar_products = get_similar_products(cfg.PRODUCT_SET_ID, generated_chair)  # Generated chair
    top = sorted(similar_products, key=lambda product: product.score, reverse=True)[:4]
    products = [(product.product.display_name, product.image.split("/")[-1], product.score) for product in
                top] or "No matching products found!"
    images = []
    for index, (product_name, product_image, product_score) in enumerate(products):
        blob_name = f"{cfg.PRODUCT_FOLDER}/{product_name}/{product_image}"
        img_blob = download_blob(storage_client, cfg.BUCKET_NAME, blob_name)
        img_blob = base64.b64encode(img_blob).decode()  # Convert to string so we can add data URI header
        img_blob = add_png_header(img_blob)
        images.append({'name': product_name, 'src': img_blob})

    generated_chair = add_png_header(generated_chair)
    resp = {
        "success": True,
        "results": images,
        "original_sketch": sketch,
        "generated_chair": generated_chair
    }
    return jsonify(resp)
    return render_template("results.html", images=images, base64_img=sketch, generated_chair=generated_chair)


def download_blob(client, bucket_name, source_blob_name):
    """Downloads a blob from the bucket."""
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    b64_img = blob.download_as_string()
    return b64_img


def upload_blob(client, bucket_name, blob, destination_blob_name):
    """Uploads blob to gcs"""
    # Append image and a timestamp
    destination_blob_name = os.path.join(destination_blob_name, f"sketch_{datetime.utcnow()}")
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(blob)


def add_png_header(data):
    return "data:image/png;base64," + data


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)
    # Add labels to chairs and use "Jag vill ha dyna" "jag vill ha armstöd" as labels and use these for product catalogue
