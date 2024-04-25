import urllib.request
import tempfile
import os
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from detect import detect
from configparser import ConfigParser
import boto3

# Load the AWS credentials from the configuration file
config = ConfigParser()
config.read('./config.ini')
access_key = config.get('aws', 'access_key')
secret_key = config.get('aws', 'secret_key')
bucket_name = config.get('aws', 'bucket_name')
base_url = config.get('aws', 'base_url')
s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)


# HTTP request handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL and query parameters
        url_parts = urlparse(self.path)
        query_params = parse_qs(url_parts.query)
        image_url = query_params.get('url', [''])[0]

        if image_url == '':
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing URL parameter')
            return

        try:
            # Split the object name to get the file name
            _, file_name = os.path.split(image_url)

            # Generate the file path based on the project directory and file name
            file_path = os.path.join("./", file_name)
            # Download the image from the URL
            s3.download_file(bucket_name, image_url, file_path)
            # Perform image detection
            gender, age = detect(image_url=file_path)
            data = {
                'image_url': image_url,
                'gender': gender,
                'age': age
            }

            # Delete the temporary file
            os.remove(file_path)
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())
            return
        response = {
            'code': 0,
            'message': "",
            'data': data
        }
        response = json.dumps(response)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())

# Run the HTTP server
def run_server():
    server_address = ('0.0.0.0', 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Server running on port 8000')
    # Start the server with HTTPS
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
