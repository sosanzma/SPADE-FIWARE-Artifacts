Use Case Example Guide: `SubscriptionManagerArtifact`
==================================================

Introduction
------------
This guide provides a detailed walkthrough of how to use the `SubscriptionManagerArtifact` example. The example demonstrates how to set up and manage subscriptions to a FIWARE Context Broker using SPADE agents and artifacts.

Example Structure
----------------
The example consists of three main files:

1. ``subscription_manager_broker_example.py``: Main script containing the example implementation
2. ``config.json``: System configuration file
3. ``payload.json``: Subscription configuration file

Prerequisites
------------
Before running the example, ensure you have:

* Python 3.7 or higher installed
* SPADE framework installed
* A running XMPP server
* A running FIWARE Context Broker
* Required Python packages::

    pip install spade aiohttp loguru

Configuration Files
------------------

System Configuration (config.json)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``config.json`` file contains the basic system settings::

    {
        "XMPP_SERVER": "sosanzma.home",
        "subscriber_artifact_name": "art_subscriber",
        "broker_port": "http://localhost:9090"
    }

* ``XMPP_SERVER``: Your XMPP server address
* ``subscriber_artifact_name``: Name for the subscriber artifact
* ``broker_port``: URL of your FIWARE Context Broker

Subscription Configuration (payload.json)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``payload.json`` file defines the subscription parameters::

    {
        "entity_type": "WasteContainer",
        "entity_id": "088",
        "watched_attributes": [],
        "q_filter": "",
        "context": [
            "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"
        ],
        "delete_all_artefact_subscriptions": true,
        "delete_subscription_identifier": "subs_v1_1",
        "subscription_identifier": "subs_v1_1",
        "delete_only": false
    }

Key Parameters:
~~~~~~~~~~~~~~
* ``entity_type``: Type of entity to monitor (e.g., "WasteContainer")
* ``entity_id``: Optional specific entity ID to monitor
* ``watched_attributes``: List of attributes to monitor (empty for all)
* ``q_filter``: Query filter for subscription
* ``context``: NGSI-LD context URL
* ``delete_all_artefact_subscriptions``: Whether to delete all existing subscriptions
* ``delete_subscription_identifier``: ID of specific subscription to delete
* ``subscription_identifier``: ID for new subscription
* ``delete_only``: If true, only performs deletion operations

Running the Example
------------------

1. Basic Setup
^^^^^^^^^^^^^
First, ensure your configuration files are properly set up with your system details.

2. Launch the Example
^^^^^^^^^^^^^^^^^^^
Run the example using Python::

    python subscription_manager_broker_example.py

3. Enter Credentials
^^^^^^^^^^^^^^^^^^
The script will prompt for two passwords:

* Subscriber artifact password
* Agent notification password

Example Usage Scenarios
----------------------

1. Basic Monitoring
^^^^^^^^^^^^^^^^^
To monitor all attributes of WasteContainer entities::

    {
        "entity_type": "WasteContainer",
        "watched_attributes": [],
        "q_filter": "",
        "delete_all_artefact_subscriptions": false,
        "delete_only": false
    }

2. Specific Attribute Monitoring
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To monitor specific attributes::

    {
        "entity_type": "WasteContainer",
        "watched_attributes": ["fillingLevel", "status"],
        "q_filter": "",
        "delete_all_artefact_subscriptions": false,
        "delete_only": false
    }

3. Filtered Monitoring
^^^^^^^^^^^^^^^^^^^^
To monitor entities matching specific conditions::

    {
        "entity_type": "WasteContainer",
        "watched_attributes": ["fillingLevel"],
        "q_filter": "fillingLevel>0.7",
        "delete_all_artefact_subscriptions": false,
        "delete_only": false
    }

4. Subscription Cleanup
^^^^^^^^^^^^^^^^^^^^^
To remove all existing subscriptions::

    {
        "entity_type": "WasteContainer",
        "delete_all_artefact_subscriptions": true,
        "delete_only": true
    }

Expected Output
--------------
When running successfully, you should see:

1. Connection confirmation messages
2. Subscription creation/deletion confirmations
3. Notification messages when subscribed entities are updated

Example output::

    INFO     Artifact art_subscriber@sosanzma.home using port 12345
    INFO     Notification server is running on http://192.168.1.100:12345
    INFO     Created subscription subs_v1_1
    INFO     Agent ready and listening to the artifact
    INFO     Received notification: {...}

Troubleshooting
--------------

Common Issues
^^^^^^^^^^^^

1. Connection Errors
~~~~~~~~~~~~~~~~~~~
* Verify XMPP server is running
* Check Context Broker URL is accessible
* Ensure ports are not blocked by firewall

2. Subscription Issues
~~~~~~~~~~~~~~~~~~~~
* Verify entity type exists in Context Broker
* Check context URL is accessible
* Validate JSON-LD context format

3. Notification Issues
~~~~~~~~~~~~~~~~~~~~
* Verify ports are open and accessible
* Check network firewall settings
* Ensure correct IP configuration

Tips and Best Practices
----------------------

1. Start Simple
^^^^^^^^^^^^^
Begin with basic monitoring before adding filters or complex configurations.

2. Monitor Logs
^^^^^^^^^^^^^
Keep an eye on the logs for subscription status and notifications.

3. Clean Up
^^^^^^^^^^
Regularly clean up unused subscriptions using the cleanup configuration.

4. Test Connectivity
^^^^^^^^^^^^^^^^^^
Test XMPP and Context Broker connectivity before setting up subscriptions.

Additional Notes
--------------
* Subscription identifiers should be unique
* Empty watched_attributes list monitors all attributes
* Q-filters support complex queries using semicolons as separators
* The example automatically handles subscription lifecycle



