import asyncio
import aiohttp
import json
import socket
from loguru import logger
import spade_artifact
from aiohttp import web
import random
import uuid


class SubscriptionManagerArtifact(spade_artifact.Artifact):
    """
    Manages subscriptions to a Context Broker and handles notifications.

    Attributes:
        broker_url (str): The URL of the Context Broker.
        recent_notifications (dict): Stores the recent notifications.
        watched_attributes (list): List of attributes that are being watched.
        config (dict): Configuration dictionary for the artifact.
        port (int): The port number for the server.
        active_subscriptions (dict): Dictionary to keep track of active subscriptions.
    """
    def __init__(self, jid, passwd, config, broker_url="http://localhost:9090"):
        """
        Initializes a SubscriptionManagerArtifact instance.

        Args:
            jid (str): The JID of the artifact.
            passwd (str): The password for the artifact.
            config (dict): Configuration dictionary for the artifact.
            broker_url (str, optional): URL of the Context Broker. Defaults to "http://localhost:9090".
        """
        super().__init__(jid, passwd)
        self.broker_url = broker_url
        self.recent_notifications = {}
        self.watched_attributes = []
        self.config = config
        self.port = None
        self.active_subscriptions = {}

    def find_free_port(self):
        """
        Finds an available port on the system to use as an endpoint.

        Returns:
            int: Available port number.
        """
        while True:
            port = random.randint(8000, 65000)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                continue
            finally:
                sock.close()

    def get_local_ip(self):
        """
        Retrieves the local IP address of the machine.

        Returns:
            str: The local IP address.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def generate_subscription_id(self):
        """
        Generates a unique identifier for the subscription.

        Returns:
            str: A unique subscription identifier.
        """
        return f"sub_{str(uuid.uuid4())[:8]}"

    async def get_active_subscriptions(self, session):
        """
        Retrieves all active subscriptions from the Context Broker.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.

        Returns:
            list: A list of active subscriptions if the request is successful; otherwise, an empty list.
        """
        try:
            async with session.get(
                f"{self.broker_url}/ngsi-ld/v1/subscriptions",
                headers={"Accept": "application/ld+json"}
            ) as response:
                if response.status == 200:
                    subscriptions = await response.json()
                    return subscriptions
                else:
                    logger.error(f"Failed to retrieve subscriptions: {await response.text()}")
                    return []
        except aiohttp.ClientError as e:
            logger.error(f"Client error occurred while retrieving subscriptions: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return []

    async def find_artifact_subscriptions(self, session):
        """
        Finds all active subscriptions of the current artifact.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.

        Returns:
            dict: A dictionary with subscription IDs and unique identifiers.
        """
        try:
            subscriptions = await self.get_active_subscriptions(session)
            artifact_identifier = str(self.jid)
            found_subscriptions = {}

            for sub in subscriptions:
                description = sub.get('description', '')
                if f"Artifact-ID: {artifact_identifier}" in description:
                    sub_id_start = description.find("Sub-ID: ") + len("Sub-ID: ")
                    sub_id_end = description.find(",", sub_id_start) if "," in description[sub_id_start:] else None
                    subscription_identifier = description[sub_id_start:sub_id_end]

                    if subscription_identifier:
                        found_subscriptions[subscription_identifier] = sub['id']
                        logger.info(f"Found subscription {subscription_identifier} ({sub['id']}) for artifact {artifact_identifier}")

            return found_subscriptions

        except Exception as e:
            logger.error(f"Error finding artifact subscriptions: {str(e)}")
            return {}

    async def delete_subscription(self, session, subscription_id):
        """
        Deletes a specific subscription from the Context Broker.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
            subscription_id (str): The ID of the subscription to be deleted.

        Returns:
            bool: True if the subscription was deleted successfully; False otherwise.
        """
        try:
            async with session.delete(
                f"{self.broker_url}/ngsi-ld/v1/subscriptions/{subscription_id}",
                headers={"Accept": "application/ld+json"}
            ) as response:
                if response.status == 204:
                    logger.info(f"Subscription {subscription_id} deleted successfully")
                    return True
                else:
                    logger.error(f"Failed to delete subscription {subscription_id}: {await response.text()}")
                    return False
        except aiohttp.ClientError as e:
            logger.error(f"Client error occurred while deleting subscription: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return False

    async def delete_subscription_by_identifier(self, session, subscription_identifier):
        """
        Deletes a subscription using its unique identifier.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
            subscription_identifier (str): The unique identifier for the subscription.

        Returns:
            bool: True if the subscription was deleted successfully; False otherwise.
        """
        try:
            subscriptions = await self.find_artifact_subscriptions(session)
            if subscription_identifier in subscriptions:
                subscription_id = subscriptions[subscription_identifier]
                success = await self.delete_subscription(session, subscription_id)
                if success:
                    logger.info(f"Deleted subscription {subscription_identifier} ({subscription_id})")
                return success
            else:
                logger.warning(f"Subscription {subscription_identifier} not found in active subscriptions")
                return False
        except Exception as e:
            logger.error(f"Error deleting subscription {subscription_identifier}: {str(e)}")
            return False

    async def delete_artifact_subscriptions(self, session):
        """
        Deletes all active subscriptions of the current artifact.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
        """
        try:
            subscriptions = await self.find_artifact_subscriptions(session)
            for sub_identifier, sub_id in subscriptions.items():
                await self.delete_subscription(session, sub_id)
                logger.info(f"Deleted subscription {sub_identifier} ({sub_id})")
            self.active_subscriptions.clear()
        except Exception as e:
            logger.error(f"Error deleting artifact subscriptions: {str(e)}")

    async def create_subscription(self, session, subscription_data, subscription_identifier):
        """
        Creates a new subscription with a specific identifier.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
            subscription_data (dict): The subscription data to send.
            subscription_identifier (str): The unique identifier for the subscription.

        Returns:
            str or None: The subscription ID if creation was successful; None otherwise.
        """
        try:
            async with session.post(
                    f"{self.broker_url}/ngsi-ld/v1/subscriptions",
                    headers={"Content-Type": "application/ld+json"},
                    json=subscription_data
            ) as response:
                if response.status == 201:
                    subscription_id = response.headers.get('Location')
                    if subscription_id:
                        self.active_subscriptions[subscription_identifier] = subscription_id
                        logger.info(f"Created subscription {subscription_identifier} ({subscription_id})")
                    return subscription_id
                else:
                    logger.error(f"Failed to create subscription: {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return None

    async def handle_notification(self, request):
        """
        Handles incoming notifications from the Context Broker.

        Args:
            request (aiohttp.web.Request): The incoming HTTP request containing the notification.

        Returns:
            aiohttp.web.Response: A response indicating the result of processing the notification.
        """
        try:
            data = await request.json()
            logger.info("Received notification")

            filtered_data = data.copy()
            for entity in filtered_data.get('data', []):
                filtered_entity = {
                    k: v for k, v in entity.items()
                    if k in self.watched_attributes or k in ['id', 'type']
                }
                entity.clear()
                entity.update(filtered_entity)

            logger.info(json.dumps(filtered_data, indent=2))

            entity_id = data['data'][0].get('id')
            notified_at = data.get('notifiedAt')

            if entity_id and notified_at:
                self.recent_notifications[entity_id] = {
                    'notifiedAt': notified_at
                }

            await self.publish(str(data))

            return web.Response(text="Notification received and processed")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {str(e)}")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as e:
            logger.error(f"Unexpected error while handling notification: {str(e)}")
            return web.Response(status=500, text="Internal Server Error")

    async def run(self):
        """
        Runs the artifact and manages subscriptions based on the configuration.
        """
        try:
            self.presence.set_available()
            local_ip = self.get_local_ip()
            self.port = self.find_free_port()
            logger.info(f"Artifact {self.jid} using port {self.port}")

            async with aiohttp.ClientSession() as session:
                if self.config.get("delete_all_artefact_subscriptions", False):
                    await self.delete_artifact_subscriptions(session)
                elif self.config.get("delete_subscription_identifier"):
                    await self.delete_subscription_by_identifier(
                        session,
                        self.config["delete_subscription_identifier"]
                    )

                if not self.config.get("delete_only", False):
                    subscription_identifier = self.config.get("subscription_identifier",
                                                              self.generate_subscription_id())
                    subscription_data = self.build_subscription_data(local_ip, subscription_identifier)

                    app = web.Application()
                    app.router.add_post("/notify", self.handle_notification)
                    runner = web.AppRunner(app)
                    await runner.setup()
                    site = web.TCPSite(runner, '0.0.0.0', self.port)
                    await site.start()

                    logger.info(f"Notification server for artifact {self.jid} is running on http://{local_ip}:{self.port}")

                    await self.create_subscription(session, subscription_data, subscription_identifier)

                logger.info(f"Artifact {self.jid} is running. Press Ctrl+C to exit.")

                while True:
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"An error occurred while running the artifact: {str(e)}")

    def build_subscription_data(self, local_ip, subscription_identifier):
        """
        Builds the subscription data, including artifact and subscription identifiers.

        Args:
            local_ip (str): Local IP address for the subscription endpoint.
            subscription_identifier (str): Unique identifier for the subscription.

        Returns:
            dict: The subscription data.
        """
        subscription_data = {
            "type": "Subscription",
            "entities": [{"type": self.config.get("entity_type")}],
            "notification": {
                "endpoint": {
                    "uri": f"http://{local_ip}:{self.port}/notify",
                    "accept": "application/json"
                }
            },
            "description": f"Artefact-ID: {self.jid}, Sub-ID: {subscription_identifier}",
            "@context": self.config.get("context", [
                "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"
            ])
        }

        entity_id = self.config.get("entity_id", "").strip()
        if entity_id:
            formatted_entity_id = self.format_entity_id(self.config.get("entity_type"), entity_id)
            subscription_data["entities"][0]["id"] = formatted_entity_id

        watched_attributes = self.config.get("watched_attributes", [])
        if watched_attributes:
            subscription_data["watchedAttributes"] = watched_attributes
            subscription_data["notification"]["attributes"] = watched_attributes
            self.watched_attributes = watched_attributes

        q_filter = self.config.get("q_filter", "").strip()
        if q_filter:
            subscription_data["q"] = q_filter

        return subscription_data

    async def cleanup(self):
        """
        Cleans up all active subscriptions when the artifact stops.
        """
        try:
            async with aiohttp.ClientSession() as session:
                await self.delete_artifact_subscriptions(session)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def format_entity_id(self, entity_type, entity_id):
        """
        Formats the entity ID to adhere to the NGSI-LD standard.

        Args:
            entity_type (str): The type of the entity.
            entity_id (str): The original entity ID.

        Returns:
            str: The formatted entity ID.
        """
        if entity_id and not entity_id.startswith("urn:ngsi-ld:"):
            return f"urn:ngsi-ld:{entity_type}:{entity_id}"
        return entity_id
