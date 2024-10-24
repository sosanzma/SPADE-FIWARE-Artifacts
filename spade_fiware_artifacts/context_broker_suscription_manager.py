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

    This class allows the creation, deletion, and management of subscriptions to a Context Broker instance,
    as well as handling incoming notifications.
    """

    def __init__(self, jid, passwd, config, broker_url="http://localhost:9090"):
        """
        Initializes the SubscriptionManagerArtifact.

        Args:
            jid (str): Jabber ID for the artifact.
            passwd (str): Password for the artifact's Jabber ID.
            config (dict): Configuration dictionary containing subscription details.
            broker_url (str, optional): The URL of the Context Broker. Defaults to "http://localhost:9090".
        """
        super().__init__(jid, passwd)
        self.broker_url = broker_url
        self.recent_notifications = {}
        self.watched_attributes = []
        self.config = config

    async def setup(self):
        """
        Sets the presence of the artifact to available.

        Attempts to set the presence status to available and logs an error if it fails.
        """
        try:
            self.presence.set_available()
        except Exception as e:
            logger.error(f"Failed to set presence: {str(e)}")

    async def create_subscription(self, session, subscription_data):
        """
        Creates a subscription with the Context Broker.

        Sends a POST request to the Context Broker to create a new subscription with the provided data.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
            subscription_data (dict): The data for the subscription to be created.

        Returns:
            str or None: The Location header from the response if the subscription is created successfully;
                         otherwise, None.
        """
        try:
            async with session.post(
                f"{self.broker_url}/ngsi-ld/v1/subscriptions",
                headers={"Content-Type": "application/ld+json"},
                json=subscription_data
            ) as response:
                if response.status == 201:
                    logger.info("Subscription created successfully")
                    return response.headers.get('Location')
                else:
                    logger.error(f"Failed to create subscription: {await response.text()}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error occurred during subscription creation: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return None

    async def handle_notification(self, request):
        """
        Handles incoming notifications from the Context Broker.

        Processes the notification data, filters it based on watched attributes, logs the information,
        updates recent notifications, and publishes the data.

        Args:
            request (aiohttp.web.Request): The incoming HTTP request containing the notification.

        Returns:
            aiohttp.web.Response: A response indicating the result of processing the notification.
        """
        try:
            data = await request.json()
            logger.info("Received notification")

            # Filter the notification data to include only watched attributes
            filtered_data = data.copy()
            for entity in filtered_data.get('data', []):
                filtered_entity = {
                    k: v for k, v in entity.items()
                    if k in self.watched_attributes or k in ['id', 'type']
                }
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

            await self.publish(str(data))

            return web.Response(text="Notification received and processed")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {str(e)}")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as e:
            logger.error(f"Unexpected error while handling notification: {str(e)}")
            return web.Response(status=500, text="Internal Server Error")

    async def get_active_subscriptions(self, session):
        """
        Retrieves all active subscriptions from the Context Broker.

        Sends a GET request to the Context Broker to fetch active subscriptions and logs their details.

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

    async def delete_subscription(self, session, subscription_id):
        """
        Deletes a specific subscription from the Context Broker.

        Sends a DELETE request to remove the subscription with the given ID.

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

    async def delete_all_subscriptions(self, session):
        """
        Deletes all active subscriptions from the Context Broker.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the requests.
        """
        try:
            subscriptions = await self.get_active_subscriptions(session)
            if not subscriptions:
                logger.info("No active subscriptions to delete.")
                return

            for sub in subscriptions:
                subscription_id = sub['id']
                await self.delete_subscription(session, subscription_id)
            logger.info("All subscriptions have been deleted.")
        except Exception as e:
            logger.error(f"Error deleting all subscriptions: {str(e)}")

    async def find_similar_subscriptions(self, session, subscription_data):
        """
        Finds subscriptions that are similar to the provided subscription data.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
            subscription_data (dict): The subscription data to compare with existing subscriptions.

        Returns:
            list: A list of similar subscriptions.
        """
        try:
            active_subscriptions = await self.get_active_subscriptions(session)
            similar_subscriptions = []
            for sub in active_subscriptions:
                if (sub.get('entities') == subscription_data.get('entities') and
                    sub.get('watchedAttributes') == subscription_data.get('watchedAttributes') and
                    sub.get('q') == subscription_data.get('q')):
                    similar_subscriptions.append(sub)
            return similar_subscriptions
        except Exception as e:
            logger.error(f"Error finding similar subscriptions: {str(e)}")
            return []

    async def delete_similar_subscriptions(self, session, similar_subscriptions):
        """
        Deletes subscriptions that are similar to the provided list.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the requests.
            similar_subscriptions (list): A list of subscriptions to delete.
        """
        for sub in similar_subscriptions:
            subscription_id = sub['id']
            await self.delete_subscription(session, subscription_id)

    async def update_subscription(self, session, subscription_id, subscription_data):
        """
        Updates an existing subscription with new data.

        Args:
            session (aiohttp.ClientSession): The HTTP session to use for the request.
            subscription_id (str): The ID of the subscription to update.
            subscription_data (dict): The new subscription data.

        Returns:
            bool: True if the subscription was updated successfully; False otherwise.
        """
        try:
            async with session.patch(
                f"{self.broker_url}/ngsi-ld/v1/subscriptions/{subscription_id}",
                headers={"Content-Type": "application/merge-patch+json"},
                json=subscription_data
            ) as response:
                if response.status == 204:
                    logger.info(f"Subscription {subscription_id} updated successfully")
                    return True
                else:
                    logger.error(f"Failed to update subscription {subscription_id}: {await response.text()}")
                    return False
        except aiohttp.ClientError as e:
            logger.error(f"Client error occurred while updating subscription: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            return False

    async def run(self):
        try:
            self.presence.set_available()

            local_ip = self.get_local_ip()
            logger.info(f"Local IP: {local_ip}")

            async with aiohttp.ClientSession() as session:
                subscription_data = self.build_subscription_data(local_ip)

                # Iniciar el servidor de notificaciones antes de crear suscripciones
                app = web.Application()
                app.router.add_post("/notify", self.handle_notification)
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, '0.0.0.0', 9999)
                await site.start()

                logger.info(f"Notification server is running on http://{local_ip}:9999")

                if self.config.get("delete_all_subscriptions", False):
                    await self.delete_all_subscriptions(session)

                similar_subscriptions = await self.find_similar_subscriptions(session, subscription_data)

                if self.config.get("delete_similar_subscriptions", False):
                    await self.delete_similar_subscriptions(session, similar_subscriptions)
                elif self.config.get("update_existing_subscription", False) and similar_subscriptions:
                    subscription_id = similar_subscriptions[0]['id']
                    await self.update_subscription(session, subscription_id, subscription_data)
                    logger.info(f"Subscription {subscription_id} has been updated.")
                else:
                    subscription_id = await self.create_subscription(session, subscription_data)
                    if subscription_id:
                        logger.info(f"Subscription ID: {subscription_id}")

                logger.info("Agent is running. Press Ctrl+C to exit.")

                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"An error occurred while running the artifact: {str(e)}")

    def build_subscription_data(self, local_ip):
        """
        Builds the subscription data based on the configuration.

        Args:
            local_ip (str): The local IP address to use in the notification endpoint.

        Returns:
            dict: The subscription data.
        """
        subscription_data = {
            "type": "Subscription",
            "entities": [{"type": self.config.get("entity_type")}],
            "notification": {
                "endpoint": {
                    "uri": f"http://{local_ip}:9999/notify",
                    "accept": "application/json"
                }
            },
            "@context": self.config.get("context", [
                "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"
            ])
        }

        entity_id = self.config.get("entity_id", "").strip()
        if entity_id:
            formatted_entity_id = self.format_entity_id(self.config.get("entity_type"), entity_id)
            subscription_data["entities"][0]["id"] = formatted_entity_id
            logger.info(f"Formatted entity ID: {formatted_entity_id}")

        watched_attributes = self.config.get("watched_attributes", [])
        if watched_attributes:
            subscription_data["watchedAttributes"] = watched_attributes
            subscription_data["notification"]["attributes"] = watched_attributes
            self.watched_attributes = watched_attributes
        else:
            self.watched_attributes = []

        q_filter = self.config.get("q_filter", "").strip()
        if q_filter:
            subscription_data["q"] = q_filter

        logger.info("Subscription data:")
        logger.info(json.dumps(subscription_data, indent=2))

        return subscription_data

    def get_local_ip(self):
        """
        Retrieves the local IP address of the machine.

        Creates a UDP socket connection to a remote address to determine the local IP address.
        If it fails, defaults to '127.0.0.1'.

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

    def format_entity_id(self, entity_type, entity_id):
        """
        Formats the entity ID to adhere to the NGSI-LD standard.

        Ensures that the entity ID starts with the 'urn:ngsi-ld:' prefix. If not, it adds the prefix.

        Args:
            entity_type (str): The type of the entity.
            entity_id (str): The original entity ID.

        Returns:
            str: The formatted entity ID.
        """
        if entity_id and not entity_id.startswith("urn:ngsi-ld:"):
            return f"urn:ngsi-ld:{entity_type}:{entity_id}"
        return entity_id
