import asyncio
import aiohttp
from aiohttp import web
import json
import socket

BROKER_URL = "http://localhost:9090"  # Update this if your Scorpio Broker is on a different host/port

# Global variable to store recent notifications and watched attributes
recent_notifications = {}
watched_attributes = []


async def create_subscription(session, subscription_data):
    async with session.post(f"{BROKER_URL}/ngsi-ld/v1/subscriptions",
                            headers={"Content-Type": "application/ld+json"},
                            json=subscription_data) as response:
        if response.status == 201:
            print("Subscription created successfully")
            print(f"Response headers: {response.headers}")
            return response.headers.get('Location')
        else:
            print(f"Failed to create subscription: {await response.text()}")
            return None


async def handle_notification(request):
    data = await request.json()
    print("Received notification:")

    # Filter the notification data to include only watched attributes
    filtered_data = data.copy()
    for entity in filtered_data.get('data', []):
        filtered_entity = {k: v for k, v in entity.items() if k in watched_attributes or k in ['id', 'type']}
        entity.clear()
        entity.update(filtered_entity)

    print(json.dumps(filtered_data, indent=2))

    # Extract key information
    notification_id = data['id']
    entity_id = data['data'][0]['id']
    notified_at = data['notifiedAt']

    # Update the recent notifications
    recent_notifications[entity_id] = {
        'id': notification_id,
        'notifiedAt': notified_at
    }

    return web.Response(text="Notification received and processed")


async def get_active_subscriptions(session):
    async with session.get(f"{BROKER_URL}/ngsi-ld/v1/subscriptions",
                           headers={"Accept": "application/ld+json"}) as response:
        if response.status == 200:
            subscriptions = await response.json()
            print("Active subscriptions:")
            for i, sub in enumerate(subscriptions, 1):
                print(
                    f"{i}. ID: {sub['id']}, Entities: {sub.get('entities', 'N/A')}, WatchedAttributes: {sub.get('watchedAttributes', 'N/A')}")
            return subscriptions
        else:
            print(f"Failed to retrieve subscriptions: {await response.text()}")
            return []


async def delete_subscription(session, subscription_id):
    async with session.delete(f"{BROKER_URL}/ngsi-ld/v1/subscriptions/{subscription_id}",
                              headers={"Accept": "application/ld+json"}) as response:
        if response.status == 204:
            print(f"Subscription {subscription_id} deleted successfully")
            return True
        else:
            print(f"Failed to delete subscription {subscription_id}: {await response.text()}")
            return False


async def review_and_delete_subscriptions(session):
    while True:
        subscriptions = await get_active_subscriptions(session)
        if not subscriptions:
            print("No active subscriptions found.")
            return

        choice = input("Enter the number of the subscription you want to delete, or 'q' to quit: ")
        if choice.lower() == 'q':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(subscriptions):
                subscription_id = subscriptions[index]['id']
                if await delete_subscription(session, subscription_id):
                    print(f"Subscription {subscription_id} has been deleted.")
                else:
                    print(f"Failed to delete subscription {subscription_id}.")
            else:
                print("Invalid subscription number.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'.")


def format_entity_id(entity_type, entity_id):
    if entity_id and not entity_id.startswith("urn:ngsi-ld:"):
        return f"urn:ngsi-ld:{entity_type}:{entity_id}"
    return entity_id


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


async def main():
    global watched_attributes
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")

    async with aiohttp.ClientSession() as session:
        # Review and delete existing subscriptions
        print("Would you like to review and delete existing subscriptions?")
        if input("Enter 'yes' for yes, any other key to skip: ").lower() == 'yes':
            await review_and_delete_subscriptions(session)

        # Get user input for new subscription
        entity_type = input("Enter the entity type to subscribe to (e.g., WasteContainer): ")
        attributes = input(
            "Enter attributes to watch and receive in notifications (comma-separated, or leave blank for all): ").split(
            ',')
        watched_attributes = [attr.strip() for attr in attributes if attr.strip()]

        entity_id = input("Enter a specific entity ID to subscribe to (or leave blank for all): ").strip()
        if entity_id:
            entity_id = format_entity_id(entity_type, entity_id)
            print(f"Formatted entity ID: {entity_id}")

        use_q_filter = input("Do you want to use a q filter? (yes/no): ").lower() == 'yes'
        q_filter = ""
        if use_q_filter:
            q_filter = input("Enter the q filter (e.g., fillingLevel>0.7): ")

        # Prepare subscription data
        subscription_data = {
            "type": "Subscription",
            "entities": [{"type": entity_type}],
            "notification": {
                "endpoint": {
                    "uri": f"http://{local_ip}:9999/notify",
                    "accept": "application/json"
                }
            },
            "@context": [
                "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"]
        }

        if entity_id:
            subscription_data["entities"][0]["id"] = entity_id

        if watched_attributes:
            subscription_data["watchedAttributes"] = watched_attributes
            subscription_data["notification"]["attributes"] = watched_attributes

        if q_filter:
            subscription_data["q"] = q_filter

        print("Subscription data:")
        print(json.dumps(subscription_data, indent=2))

        # Create new subscription
        subscription_id = await create_subscription(session, subscription_data)
        if subscription_id:
            print(f"Subscription ID: {subscription_id}")

        # Get active subscriptions
        await get_active_subscriptions(session)

    # Set up notification server
    app = web.Application()
    app.router.add_post("/notify", handle_notification)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9999)
    await site.start()

    print(f"Notification server is running on http://{local_ip}:9999")
    print("Press Ctrl+C to exit")

    # Keep the server running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())