import sys
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
# Verify it works
import os
import json
import random
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


# set up slack client with token
token = get_secret(secret_name, secret_region)
client = WebClient(token = token)


def send_message(channel_id):
    """
    Given channel id, sends the first secret santa message
    """
    response = client.chat_postMessage(
        channel=channel_id, 
        text="Let's play secret santa!",
    )
    return response['ts']


def send_message_handler(event, context):
    output = {
        'timestamp': send_message(channel_id)
    }
    return json.dumps(output)


def collect_response(channel_id, timestamp):
    """
    Given channel id and timestamp of message, 
    collects list of all users that reacted to message
    note that it does not discriminate between different reacts
    """
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
    print(event)
    print(event['timestamp'])
    participants = collect_response(channel_id, event['timestamp'])
    responses = assign_gifts(participants)
    write_to_queue()
    return json.dumps(responses)


def assign_gifts(participants):
    """
    Given a list of slack users, creates list 
    of secret santa pairs 
    """
    pairs=[]
    total_num = len(participants)
    if total_num >1:
        random.shuffle(participants)
        for index in total_num-1:
            pairs+= (participants[index],participants[index+1])
        pairs+= (participants[total_num], participants[0])
    return pairs


def write_to_queue():
    # write to queue
    sqs = boto3.resource('sqs')
    QUEUE_URL = os.environ['QUEUE_URL']
    queue = sqs.Queue(QUEUE_URL)
    response = queue.send_message(
        MessageBody='myMessage'
    )


def send_santa_message():
    """
    Given a pair of user, send appropriate secret santa message
    """
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