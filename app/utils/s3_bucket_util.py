import os

import boto3
from botocore.exceptions import ClientError

from app.errors import BaseAppException
from app.utils.ssm_util import get_cached_parameter


def upload_file(key: str, body: bytes, content_type: str) -> str:
    """
    Upload a file to S3 using server-side encryption with KMS.

    :param key: The S3 object key.
    :param body: The file content as bytes.
    :param content_type: The MIME type of the file.
    :return: The URL of the uploaded file.
    :raises Exception: If the upload fails.
    """
    try:
        # Retrieve SSM parameters for S3 bucket name and KMS key ID.
        bucket = get_cached_parameter(os.environ.get("S3_BUCKET_NAME"))
        kms_key_id = get_cached_parameter(os.environ.get("S3_KMS_KEY_ID"))

        # Create an S3 client.
        s3_client = boto3.client("s3")

        # Upload the file using put_object.
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=kms_key_id,
        )

        # Determine the S3 region to construct the URL.
        region = s3_client.meta.region_name

        # Construct the URL for accessing the uploaded file.
        if region == "us-east-1":
            location = f"https://{bucket}.s3.amazonaws.com/{key}"
        else:
            location = f"https://{bucket}.s3-{region}.amazonaws.com/{key}"

        return location

    except ClientError as error:
        raise BaseAppException(f"Error uploading file: {error}") from error
