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


secret_region = os.environ['SECRET_REGION']
secret_name = os.environ['SANTA_BOT_TOKEN']
channel_id = os.environ['CHANNEL_ID']

@lru_cache
def get_secret(name, region):
    """
    Given secrets name and aws region,
    retrieves secrets from the AWS secrets manager
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    get_secret_value_response = client.get_secret_value(
        SecretId=name
    )
    # Decrypts secret using the associated KMS CMK.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)['token']
    else:
        decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        return json.loads(decoded_binary_secret)['token']


token = get_secret(secret_name, secret_region)
client = WebClient(token = token)

def send_message(channel_id):
    response = client.chat_postMessage(
        channel=channel_id, 
        text="Let's play secret santa!",
    )
    return response['ts']


def send_message_handler(event, context):
    return send_message(channel_id)


def collect_response(channel_id):
    response = client.reactions_get(
        channel = channel_id,
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


def collect_response_handler(event, context):
    return collect_response(channel_id, token)

def assign_gifts(participants):
    # this should be a lambda that writes a batch into the queue
    # this should push a bunch of stuff into the queue
    pass



def send_santa_message():
    # [gift_giver, gift_receiver] = pairs
    message = client.conversations_open(
        users = ["U02AMAUGC4V"],
    )
    message_id = message['channel']['id']
    santa = client.chat_postMessage(
    channel=message_id, 
    text="Hello, your secret santa is <@U02AMAUGC4V>",
)

def send_santa_message_handler(event, context):
    send_santa_message()

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