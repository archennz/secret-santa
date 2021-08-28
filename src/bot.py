import sys
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
# Verify it works
import os
import json
from functools import lru_cache
from slack_sdk import WebClient
import boto3
import base64
from botocore.exceptions import ClientError


client = WebClient()
secret_name = os.environ['SANTA_BOT_TOKEN']
channel_id = os.environ['CHANNEL_ID']
# secret_name = "SantaBotToken"
# channel_id = "C02AWHL5S3W"

@lru_cache
def get_secret(secret_name):
    region_name = "ap-southeast-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return json.loads(secret)['token']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return json.loads(decoded_binary_secret)['token']


token = get_secret(secret_name)


def send_message(event, context):
    response = client.chat_postMessage(
        channel=channel_id, 
        text="Let's play secret santa!",
        token=token
    )
    return response['ts']


def collect_response(event, context):
    response = client.reactions_get(
        channel = channel_id,
        token = token,
        timestamp = "1630140294.000200"
    )
    # need to handle when the message isnt there
    # need to handle when there are no reactions
    # check response okay is true
    print(response)
    reactions = response['message'].get('reactions', [])
    print(reactions)
    participants = []
    for reaction in reactions:
        print(reaction)
        participants += reaction['users']
    return list(set(participants))

def assign_gifts(participants):
    # this should be a lambda that writes a batch into the queue
    # this should push a bunch of stuff into the queue
    pass



def send_santa_message(event, context):
    # [gift_giver, gift_receiver] = pairs
    message = client.conversations_open(
        token = token,
        users = ["U02AMAUGC4V"],
    )
    message_id = message['channel']['id']
    santa = client.chat_postMessage(
    channel=message_id, 
    text="Hello, your secret santa is <@U02AMAUGC4V>",
    token=token
)

# try:
#     # Call the chat.postMessage method using the WebClient
#     result = client.chat_postMessage(
#         channel=channel_id, 
#         text="Let's play secret santa!",
#         token=token
#     )
#     print(result['ts'])
#     logging.info(result)
# except SlackApiError as e:
#     logging.error(f"Error posting message: {e}")