import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load .env file from current directory
load_dotenv()

# Get GCP storage settings from environment
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
GCP_STORAGE_BUCKET_NAME = os.getenv('GCP_STORAGE_BUCKET_NAME')
GCP_SERVICE_ACCOUNT_FILE = os.getenv('GCP_SERVICE_ACCOUNT_FILE')

# Path to a test file to upload (change as needed)
TEST_FILE_PATH = '/home/nwodo/Downloads/WhatsApp Image 2025-08-07 at 20.00.10.jpeg'
GCS_DESTINATION_BLOB = 'test_upload_from_script.txt'

def main():
    # # Create a test file to upload
    # with open(TEST_FILE_PATH, 'w') as f:
    #     f.write('This is a test file for GCP Storage upload.\n')
    
    # Authenticate using service account
    credentials = service_account.Credentials.from_service_account_file(GCP_SERVICE_ACCOUNT_FILE)
    client = storage.Client(project=GCP_PROJECT_ID, credentials=credentials)
    bucket = client.bucket(GCP_STORAGE_BUCKET_NAME)
    blob = bucket.blob(GCS_DESTINATION_BLOB)
    
    print(f"Uploading {TEST_FILE_PATH} to gs://{GCP_STORAGE_BUCKET_NAME}/{GCS_DESTINATION_BLOB} ...")
    try:
        blob.upload_from_filename(TEST_FILE_PATH)
        blob.make_public()  # <-- Add this line
        print("✅ Upload successful!")
        print(f"Public URL: {blob.public_url}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
    
    # Clean up test file
    os.remove(TEST_FILE_PATH)

if __name__ == '__main__':
    main()
