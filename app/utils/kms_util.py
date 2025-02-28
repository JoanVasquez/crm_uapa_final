import base64
import os

import boto3
from botocore.exceptions import ClientError

from app.utils.logger import get_logger

logger = get_logger(__name__)

region = os.environ.get("AWS_REGION", "us-east-1")
kms_client = boto3.client("kms", region_name=region)


def encrypt_password(password: str, kms_key_id: str) -> str:
    """
    Encrypt the given password using AWS KMS and return it as a base64
    encoded string.

    :param password: The plaintext password.
    :param kms_key_id: The AWS KMS Key ID to use for encryption.
    :return: The encrypted password as a base64 encoded string.
    :raises Exception: If encryption fails.
    """
    try:
        response = kms_client.encrypt(KeyId=kms_key_id,
                                      Plaintext=password.encode("utf-8"))

        ciphertext_blob = response.get("CiphertextBlob")
        if not ciphertext_blob:
            logger.error(
                "Failed to encrypt password: No CiphertextBlob returned")
            raise Exception("Failed to encrypt password")

        # Encode the ciphertext blob to a base64 string
        encrypted_password = base64.b64encode(ciphertext_blob).decode("utf-8")
        return encrypted_password

    except ClientError as error:
        logger.error(f"Error encrypting password: {error}", exc_info=True)
        raise Exception("Failed to encrypt password") from error


def decrypt_password(encrypted_password: str, kms_key_id: str) -> str:
    """
    Decrypt the given encrypted password (base64 encoded) using AWS KMS
    and return the plaintext.

    :param encrypted_password: The encrypted password as a base64
                               encoded string.
    :param kms_key_id: The AWS KMS Key ID used for decryption.
    :return: The decrypted plaintext password.
    :raises Exception: If decryption fails.
    """
    # Decode the base64 encoded encrypted password to get the
    # ciphertext blob.
    # ciphertext blob.

    try:
        ciphertext_blob = base64.b64decode(encrypted_password)

        response = kms_client.decrypt(KeyId=kms_key_id,
                                      CiphertextBlob=ciphertext_blob)

        plaintext = response.get("Plaintext")
        if not plaintext:
            logger.error("Failed to decrypt password: No Plaintext returned")
            raise Exception("Failed to decrypt password")

        return plaintext.decode("utf-8")

    except ClientError as error:
        logger.error(f"Error decrypting password: {error}", exc_info=True)
        raise Exception("Failed to decrypt password") from error
