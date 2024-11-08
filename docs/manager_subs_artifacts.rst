`SubscriptionManagerArtifact`
===============================

Overview
--------
The ``SubscriptionManagerArtifact`` manages NGSI-LD subscriptions with a FIWARE Context Broker. It extends the base ``spade_artifact.Artifact`` class and provides comprehensive functionality for subscription management, notification handling, and artifact-agent communication.

Class Architecture
----------------

Core Components
^^^^^^^^^^^^^
The class is structured around several key components:

1. **Subscription Management**
   - Creation and deletion of subscriptions
   - Tracking active subscriptions
   - Subscription identifier generation

2. **Notification Handling**
   - HTTP server for receiving notifications
   - Notification processing and filtering
   - Data publishing to focused agents

3. **Network Configuration**
   - Dynamic port allocation
   - IP address management
   - Endpoint configuration

Key Attributes
^^^^^^^^^^^^
.. code-block:: python

    class SubscriptionManagerArtifact(spade_artifact.Artifact):
        def __init__(self, jid, passwd, config, broker_url="http://localhost:9090"):
            self.broker_url = broker_url
            self.recent_notifications = {}
            self.watched_attributes = []
            self.config = config
            self.port = None
            self.active_subscriptions = {}

- ``broker_url``: Context Broker endpoint
- ``recent_notifications``: Cache of received notifications
- ``watched_attributes``: List of monitored attributes
- ``config``: Subscription configuration
- ``port``: Dynamic port for notification server
- ``active_subscriptions``: Dictionary of current subscriptions

Core Functionality
----------------

Subscription Creation
^^^^^^^^^^^^^^^^^^
.. code-block:: python

    async def create_subscription(self, session, subscription_data, subscription_identifier):
        """Creates a new subscription in the Context Broker."""

The method:
1. Sends POST request to Context Broker
2. Handles response and stores subscription ID
3. Updates active_subscriptions dictionary
4. Logs creation status

Subscription Deletion
^^^^^^^^^^^^^^^^^^
.. code-block:: python

    async def delete_subscription(self, session, subscription_id):
        """Deletes a subscription from the Context Broker."""

    async def delete_subscription_by_identifier(self, session, subscription_identifier):
        """Deletes a subscription using its unique identifier."""

    async def delete_artifact_subscriptions(self, session):
        """Deletes all subscriptions associated with this artifact."""

These methods provide different levels of subscription cleanup:
- Individual subscription deletion
- Identifier-based deletion
- Bulk deletion of artifact subscriptions

Notification Handling
^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    async def handle_notification(self, request):
        """Processes incoming notifications from the Context Broker."""

The notification handler:
1. Parses incoming JSON data
2. Filters attributes based on configuration
3. Updates recent_notifications cache
4. Publishes data to focused agents
5. Returns appropriate HTTP response

Integration in run() Method
-------------------------

The ``run()`` method orchestrates all components:

.. code-block:: python

    async def run(self):
        try:
            self.presence.set_available()
            local_ip = self.get_local_ip()
            self.port = self.find_free_port()

            async with aiohttp.ClientSession() as session:
                # Subscription cleanup if configured
                if self.config.get("delete_all_artifact_subscriptions", False):
                    await self.delete_artifact_subscriptions(session)
                elif self.config.get("delete_subscription_identifier"):
                    await self.delete_subscription_by_identifier(
                        session,
                        self.config["delete_subscription_identifier"])

                # Create new subscription if not delete-only mode
                if not self.config.get("delete_only", False):
                    subscription_identifier = self.config.get("subscription_identifier",
                                                          self.generate_subscription_id())
                    subscription_data = self.build_subscription_data(local_ip, subscription_identifier)

                    # Set up notification server
                    app = web.Application()
                    app.router.add_post("/notify", self.handle_notification)
                    runner = web.AppRunner(app)
                    await runner.setup()
                    site = web.TCPSite(runner, '0.0.0.0', self.port)
                    await site.start()

                    # Create subscription
                    await self.create_subscription(session, subscription_data, subscription_identifier)

                while True:
                    await asyncio.sleep(1)

Execution Flow:
1. Sets artifact availability
2. Configures network settings
3. Performs subscription cleanup if needed
4. Sets up notification server
5. Creates new subscription
6. Maintains continuous operation

Usage Patterns
-------------

1. Basic Subscription Management
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    config = {
        "entity_type": "Device",
        "watched_attributes": ["temperature", "humidity"],
        "subscription_identifier": "env_monitor"
    }

    artifact = SubscriptionManagerArtifact(
        jid="monitor@xmpp.server",
        passwd="password",
        config=config,
        broker_url="http://broker:1026"
    )

2. Filtered Subscriptions
^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    config = {
        "entity_type": "Device",
        "watched_attributes": ["temperature"],
        "q_filter": "temperature>30",
        "subscription_identifier": "high_temp_alert"
    }

3. Subscription Cleanup
^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    config = {
        "delete_all_artifact_subscriptions": True,
        "delete_only": True
    }

4. Specific Entity Monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    config = {
        "entity_type": "Device",
        "entity_id": "device001",
        "watched_attributes": ["status"],
        "subscription_identifier": "device_status"
    }

Advanced Features
---------------

Dynamic Port Allocation
^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    def find_free_port(self):
        """Finds an available port for the notification server."""

- Randomly selects ports in range 8000-65000
- Tests port availability
- Returns first available port

IP Address Management
^^^^^^^^^^^^^^^^^^
.. code-block:: python

    def get_local_ip(self):
        """Retrieves the local IP address."""

- Determines machine's IP address
- Handles various network configurations
- Falls back to localhost if needed

Subscription Data Building
^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    def build_subscription_data(self, local_ip, subscription_identifier):
        """Constructs subscription payload."""

Builds NGSI-LD subscription with:
- Entity specifications
- Notification endpoint
- Attribute filters
- Query conditions


Integration Examples
------------------

1. **With SPADE Agent**
^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    class MonitorAgent(Agent):
        async def setup(self):
            artifact = SubscriptionManagerArtifact(...)
            await artifact.start()
            await self.artifacts.focus(artifact.jid, self.handle_notification)

2. **Multiple Subscriptions**
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    async def manage_subscriptions():
        artifact = SubscriptionManagerArtifact(...)
        configs = [config1, config2, config3]
        for config in configs:
            artifact.config = config
            await artifact.start()

3. **Custom Notification Processing**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    class CustomSubscriptionManager(SubscriptionManagerArtifact):
        async def handle_notification(self, request):
            data = await request.json()
            # Custom processing
            await self.publish(processed_data)

Conclusion
---------
The ``SubscriptionManagerArtifact`` provides a robust foundation for managing NGSI-LD subscriptions in a FIWARE environment. Its modular design, comprehensive feature set, and flexible configuration options make it suitable for a wide range of application scenarios.