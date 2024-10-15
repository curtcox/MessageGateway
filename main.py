import functions_framework
from google.cloud import pubsub_v1
import json
import time
import os

# Constants
DEFAULT_TIMEOUT = 60  # seconds
PROJECT_ID = os.environ.get('PROJECT_ID')
INPUT_TOPIC = os.environ.get('INPUT_TOPIC')
OUTPUT_TOPIC = os.environ.get('OUTPUT_TOPIC')

# Initialize Pub/Sub clients
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# Prepare Pub/Sub paths
SUBSCRIPTION_PATH = subscriber.subscription_path(PROJECT_ID, f"{INPUT_TOPIC}-sub")
INPUT_TOPIC_PATH = publisher.topic_path(PROJECT_ID, INPUT_TOPIC)
OUTPUT_TOPIC_PATH = publisher.topic_path(PROJECT_ID, OUTPUT_TOPIC)

def get_waiting_message_count():
    response = subscriber.get_subscription(request={"subscription": SUBSCRIPTION_PATH})
    return response.num_pending_messages

def add_message_to_input_queue(message):
    future = publisher.publish(INPUT_TOPIC_PATH, message.encode('utf-8'))
    return future.result()

def pull_messages(max_messages=10):
    return subscriber.pull(request={"subscription": SUBSCRIPTION_PATH, "max_messages": max_messages})

def publish_message(message_data):
    future = publisher.publish(OUTPUT_TOPIC_PATH, message_data)
    return future.result()

def acknowledge_messages(ack_ids):
    subscriber.acknowledge(request={"subscription": SUBSCRIPTION_PATH, "ack_ids": ack_ids})

def process_message_batch(received_messages):
    ack_ids = []
    for received_message in received_messages:
        print(f"Received message: {received_message.message.data}")
        message_id = publish_message(received_message.message.data)
        print(f"Published message ID: {message_id}")
        ack_ids.append(received_message.ack_id)
    return ack_ids

def process_messages_with_timeout(timeout):
    start_time = time.time()
    messages_processed = 0
    total_messages = get_waiting_message_count()

    while time.time() - start_time < timeout:
        response = pull_messages()

        if not response.received_messages:
            print(f"No more messages to process. Processed {messages_processed} out of {total_messages} messages.")
            return messages_processed, total_messages, False  # Indicates that we finished processing all messages

        ack_ids = process_message_batch(response.received_messages)
        messages_processed += len(ack_ids)

        if ack_ids:
            acknowledge_messages(ack_ids)

    print(f"Timeout reached. Processed {messages_processed} out of {total_messages} messages.")
    return messages_processed, total_messages, True  # Indicates that we exited due to timeout

def handle_get_waiting_messages():
    waiting_messages = get_waiting_message_count()
    return f'Number of messages waiting in the input queue: {waiting_messages}', 200

def handle_add_message(request):
    request_json = request.get_json(silent=True)
    if not request_json or 'message' not in request_json:
        return 'Bad Request: JSON body with "message" field required', 400

    message = request_json['message']
    message_id = add_message_to_input_queue(message)
    return f'Message added to input queue. Message ID: {message_id}', 200

def handle_process_messages(request):
    request_json = request.get_json(silent=True)
    timeout = request_json.get('timeout', DEFAULT_TIMEOUT) if request_json else DEFAULT_TIMEOUT

    processed, total, timeout_reached = process_messages_with_timeout(timeout)
    if timeout_reached:
        return f'Timeout reached: processed {processed} out of {total} messages', 200
    else:
        return f'All messages processed: {processed} out of {total} messages', 200

@functions_framework.http
def handle_http_request(request):
    if request.method == 'GET' and request.path == '/':
        return handle_get_waiting_messages()
    elif request.method == 'POST' and request.path == '/add':
        return handle_add_message(request)
    elif request.method == 'POST' and request.path == '/process':
        return handle_process_messages(request)
    else:
        return 'Not Found', 404

@functions_framework.cloud_event
def handle_pubsub_wakeup(cloud_event):
    data = json.loads(cloud_event.data['message']['data'])
    timeout = data.get('timeout', DEFAULT_TIMEOUT)

    processed, total, timeout_reached = process_messages_with_timeout(timeout)
    if timeout_reached:
        return f'Timeout reached: processed {processed} out of {total} messages', 200
    else:
        return f'All messages processed: {processed} out of {total} messages', 200