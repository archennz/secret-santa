import logging
import os
import json
import random
from functools import lru_cache
from slack_sdk import WebClient
import boto3
import base64
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.DEBUG)

secret_region = os.environ['SECRET_REGION']
secret_name = os.environ['SANTA_BOT_TOKEN']
channel_id = os.environ['CHANNEL_ID']

@lru_cache
def get_secret(name, region):
    """
    Given secrets name and aws region,
    retrieves secrets from the AWS secrets manager
    """
    logging.debug("Creating aws secret manager session")
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
    else:
        secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    logging.info("Token retrieved from secrets manager")
    return json.loads(secret)['token']


# set up slack client with token
token = get_secret(secret_name, secret_region)
client = WebClient(token = token)


def send_message(channel_id):
    """
    Given channel id, sends the first secret santa message
    """
    logging.info("Send start secret santa message")
    response = client.chat_postMessage(
        channel=channel_id, 
        text="Let's play secret santa!",
    )
    return response['ts']


def collect_response(channel_id, timestamp):
    """
    Given channel id and timestamp of message, 
    collects list of all users that reacted to message
    note that it does not discriminate between different reacts
    """
    print("Getting reactions")
    response = client.reactions_get(
        channel = channel_id,
        timestamp = timestamp
    )
    print(response)
    # need to handle when the message isnt there
    # need to handle when there are no reactions
    # check response okay is true
    reactions = response['message'].get('reactions', [])
    print("reactions")
    participants = []
    for reaction in reactions:
        print(reaction)
        participants += reaction['users']
    logging.info("Finished getting participants")
    print(participants)
    return list(set(participants))


def assign_gifts(participants):
    """
    Given a list of slack users, creates list 
    of secret santa pairs 
    """
    print("Starting to pair up participants")
    pairs=[]
    total_num = len(participants)
    if total_num >1:
        random.shuffle(participants)
        for index in range(total_num-1):
            pairs.append((participants[index],participants[index+1]))
            print(pairs)
        pairs.append((participants[total_num-1], participants[0]))
    print("completed pairing:")
    print(pairs)
    return pairs


def write_to_queue(message):
    """
    Writes message to queue
    """
    sqs = boto3.resource('sqs')
    QUEUE_URL = os.environ['QUEUE_URL']
    queue = sqs.Queue(QUEUE_URL)
    response = queue.send_message(
        MessageBody=message
    )
    logging.info("Pushed message to queue")
    print(message)


def send_santa_message(pair):
    """
    Given a pair of user, send appropriate secret santa message
    """
    (gift_giver, gift_receiver) = pair
    message = client.conversations_open(
        users = [gift_giver],
    )
    message_id = message['channel']['id']
    santa = client.chat_postMessage(
    channel=message_id, 
    text="Hello, your secret santa is <@{}>".format(gift_receiver),
)


def send_message_handler(event, context):
    output = {
        'timestamp': send_message(channel_id)
    }
    return json.dumps(output)


def collect_response_handler(event, context):
    print(event)
    print(event['timestamp'])
    participants = collect_response(channel_id, event['timestamp'])
    pairs = assign_gifts(participants)
    for pair in pairs:
        message_raw = {'pair': pair}
        write_to_queue(json.dumps(message_raw))
    return json.dumps({'pairs': pairs})


def send_santa_message_handler(event, context):
    print(event)
    print(event['Records'])
    message = event['Records'][0]['body']
    print(message)
    pair = json.loads(message)['pair']
    print(pair)
    send_santa_message(pair)



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