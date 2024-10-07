import asyncio
import aiohttp
import json
import socket
from loguru import logger
import spade_artifact
from aiohttp import web


class SubscriptionManagerArtifact(spade_artifact.Artifact):
    """
    An artifact for managing subscriptions in a Context Broker.

    This class allows the creation, deletion, and management of subscriptions to a Context Broker instance, as well as handling incoming notifications.

    Attributes:
        broker_url (str): The URL of the Context Broker.
        recent_notifications (dict): Dictionary to store recent notifications.
        watched_attributes (list): List of attributes to watch for notifications.

    Args:
        jid (str): Jabber ID for the artifact.
        passwd (str): Password for the artifact's Jabber ID.
        broker_url (str): The URL of the Context Broker.
    """
    def __init__(self, jid, passwd, broker_url="http://localhost:9090"):
        super().__init__(jid, passwd)
        self.broker_url = broker_url
        self.recent_notifications = {}
        self.watched_attributes = []

    async def setup(self):
        try:
            self.presence.set_available()
        except Exception as e:
            logger.error(f"Failed to set presence: {str(e)}")

    async def create_subscription(self, session, subscription_data):
        async with session.post(f"{self.broker_url}/ngsi-ld/v1/subscriptions",
                                headers={"Content-Type": "application/ld+json"},
                                json=subscription_data) as response:
            if response.status == 201:
                logger.info("Subscription created successfully")
                return response.headers.get('Location')
            else:
                logger.error(f"Failed to create subscription: {await response.text()}")
                return None

    async def handle_notification(self, request):
        data = await request.json()
        logger.info("Received notification")

        # Filter the notification data to include only watched attributes
        filtered_data = data.copy()
        for entity in filtered_data.get('data', []):
            filtered_entity = {k: v for k, v in entity.items() if k in self.watched_attributes or k in ['id', 'type']}
            entity.clear()
            entity.update(filtered_entity)

        logger.info(json.dumps(filtered_data, indent=2))

        # Extract key information
        entity_id = data['data'][0].get('id')
        notified_at = data.get('notifiedAt')

        if entity_id and notified_at:
            self.recent_notifications[entity_id] = {
                'notifiedAt': notified_at
            }

        return web.Response(text="Notification received and processed")

    async def get_active_subscriptions(self, session):
        async with session.get(f"{self.broker_url}/ngsi-ld/v1/subscriptions",
                               headers={"Accept": "application/ld+json"}) as response:
            if response.status == 200:
                subscriptions = await response.json()
                logger.info("Active subscriptions:")
                for i, sub in enumerate(subscriptions, 1):
                    logger.info(
                        f"{i}. ID: {sub['id']}, Entities: {sub.get('entities', 'N/A')}, WatchedAttributes: {sub.get('watchedAttributes', 'N/A')}")
                return subscriptions
            else:
                logger.error(f"Failed to retrieve subscriptions: {await response.text()}")
                return []

    async def delete_subscription(self, session, subscription_id):
        async with session.delete(f"{self.broker_url}/ngsi-ld/v1/subscriptions/{subscription_id}",
                                  headers={"Accept": "application/ld+json"}) as response:
            if response.status == 204:
                logger.info(f"Subscription {subscription_id} deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete subscription {subscription_id}: {await response.text()}")
                return False

    async def review_and_delete_subscriptions(self, session):
        subscriptions = await self.get_active_subscriptions(session)
        if not subscriptions:
            logger.info("No active subscriptions found.")
            return

        choice = input("Enter the number of the subscription you want to delete, or 'q' to quit: ")
        if choice.lower() == 'q':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(subscriptions):
                subscription_id = subscriptions[index]['id']
                if await self.delete_subscription(session, subscription_id):
                    logger.info(f"Subscription {subscription_id} has been deleted.")
                else:
                    logger.error(f"Failed to delete subscription {subscription_id}.")
            else:
                logger.warning("Invalid subscription number.")
        except ValueError:
            logger.warning("Invalid input. Please enter a number or 'q'.")

    async def run(self):
        local_ip = self.get_local_ip()
        logger.info(f"Local IP: {local_ip}")

        async with aiohttp.ClientSession() as session:
            if input("Would you like to review and delete existing subscriptions? (yes/no): ").lower() == 'yes':
                await self.review_and_delete_subscriptions(session)

            entity_type = input("Enter the entity type to subscribe to (e.g., WasteContainer): ")
            attributes = input("Enter attributes to watch and receive in notifications (comma-separated, or leave blank for all): ").split(',')
            self.watched_attributes = [attr.strip() for attr in attributes if attr.strip()]

            entity_id = input("Enter a specific entity ID to subscribe to (or leave blank for all): ").strip()
            if entity_id:
                entity_id = self.format_entity_id(entity_type, entity_id)
                logger.info(f"Formatted entity ID: {entity_id}")

            use_q_filter = input("Do you want to use a q filter? (yes/no): ").lower() == 'yes'
            q_filter = ""
            if use_q_filter:
                q_filter = input("Enter the q filter (e.g., fillingLevel>0.7): ")

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

            if self.watched_attributes:
                subscription_data["watchedAttributes"] = self.watched_attributes
                subscription_data["notification"]["attributes"] = self.watched_attributes

            if q_filter:
                subscription_data["q"] = q_filter

            logger.info("Subscription data:")
            logger.info(json.dumps(subscription_data, indent=2))

            subscription_id = await self.create_subscription(session, subscription_data)
            if subscription_id:
                logger.info(f"Subscription ID: {subscription_id}")

            app = web.Application()
            app.router.add_post("/notify", self.handle_notification)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', 9999)
            await site.start()

            logger.info(f"Notification server is running on http://{local_ip}:9999")
            logger.info("Press Ctrl+C to exit")

            while True:
                await asyncio.sleep(1)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def format_entity_id(self, entity_type, entity_id):
        if entity_id and not entity_id.startswith("urn:ngsi-ld:"):
            return f"urn:ngsi-ld:{entity_type}:{entity_id}"
        return entity_id


if __name__ == "__main__":
    jid = "your_jid"
    passwd = "your_password"
    artifact = SubscriptionManagerArtifact(jid, passwd)
    asyncio.run(artifact.run())