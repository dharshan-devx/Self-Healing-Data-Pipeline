import os
import json
import time
import random
from kafka import KafkaProducer
from faker import Faker

# Load environment variables
# KAFKA_BROKER is passed from docker-compose.yml
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'broker:9092')
TOPIC = "user_events"
SCHEMA_CHANGE_THRESHOLD = 500  # Introduce schema change after 500 records

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
print(f"Connected to Kafka broker at {KAFKA_BROKER}")

# Initialize Faker for generating fake data
fake = Faker()

def generate_user_event(record_number, with_new_field=False):
    """
    Generates a single fake user event.
    
    :param record_number: The sequential number of the record.
    :param with_new_field: Boolean to simulate a schema change.
    :return: A dictionary representing a user event.
    """
    user_id = random.randint(1000, 9999)
    event_type = random.choice(['page_view', 'add_to_cart', 'purchase'])
    timestamp = int(time.time() * 1000)

    event_data = {
        'user_id': user_id,
        'event_id': fake.uuid4(),
        'event_type': event_type,
        'timestamp': timestamp,
        'product_id': random.randint(10000, 99999),
        'category': random.choice(['electronics', 'apparel', 'books', 'home_goods']),
        'price': round(random.uniform(10.0, 500.0), 2),
    }

    # Simulate a schema drift by adding a new field
    if with_new_field:
        event_data['referral_source'] = random.choice(['google', 'facebook', 'email', 'direct'])

    return event_data

if __name__ == "__main__":
    record_count = 0
    try:
        while True:
            # Check if we should introduce a schema change
            schema_change = (record_count > SCHEMA_CHANGE_THRESHOLD and record_count % 2 == 0)
            
            # Generate and send the event
            event = generate_user_event(record_count, with_new_field=schema_change)
            producer.send(TOPIC, value=event)
            
            print(f"Sent record {record_count}: {event['event_type']} event from user {event['user_id']}")
            
            record_count += 1
            time.sleep(1) # Send one event per second
            
    except KeyboardInterrupt:
        print("\nStopping data producer.")
        producer.flush()
        producer.close()