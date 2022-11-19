import boto3
from dotenv import dotenv_values
env = dotenv_values('.env.local')

def r2_retrieve(id):
    s3 = boto3.resource('s3',
        endpoint_url = f"https://{env['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id = env['R2_API_ID'],
        aws_secret_access_key = env['R2_API_KEY']
    )
    response = s3.Object(env['R2_BUCKET'], id).get()
    return response['Body'].read().decode("utf-8")

def r2_upload(file_path, id):
    s3 = boto3.resource('s3',
        endpoint_url = f"https://{env['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id = env['R2_API_ID'],
        aws_secret_access_key = env['R2_API_KEY']
    )
    s3.meta.client.upload_file(file_path, env['R2_BUCKET'], id)
