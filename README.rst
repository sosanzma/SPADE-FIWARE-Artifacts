SPADE-FIWARE-Artifacts
=====================

.. image:: https://readthedocs.org/projects/spade-fiware-artifacts/badge/?version=latest
    :target: https://spade-fiware-artifacts.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/actions/workflow/status/sosanzma/spade-fiware-artifacts/python-app.yml
        :target: https://github.com/sosanzma/spade-fiware-artifacts/actions
        :alt: Build Status

.. image:: https://coveralls.io/repos/github/sosanzma/SPADE-FIWARE-Artifacts/badge.svg?branch=main
    :target: https://coveralls.io/github/sosanzma/SPADE-FIWARE-Artifacts?branch=main

Overview
--------

SPADE-FIWARE-Artifacts is a Python library that bridges SPADE (Smart Python Agent Development Environment) with FIWARE Context Brokers. It provides a robust toolkit for multi-agent systems to interact with FIWARE's context management system, supporting both Orion and Scorpio Context Brokers through NGSI-LD.

Key Features
-----------

- **NGSI-LD Support**: Full compatibility with FIWARE's NGSI-LD API
- **Asynchronous Operations**: Built on asyncio for efficient non-blocking operations
- **Flexible Data Processing**: Customizable data transformation and handling
- **Configurable JSON Templates**: Allows customized JSON templates for data structuring and flexible formatting.

Core Components
-------------

In a multi-agent system powered by SPADE, agents can use the artifacts to interact with the environment. In this case,
two artifacts have been created that allow agents to interact with FIWARE's context brokers, Scorpio and Orion.
This artifacts are the following:

InserterArtifact
~~~~~~~~~~~~~~~

A powerful component for managing entity data in FIWARE Context Brokers:

- **Entity Management**:
    - Create new entities with complex attributes
    - Update existing entities (full or partial updates)
    - Handle different attribute types (Properties, GeoProperties, Relationships)

- **Data Processing**:
    - Custom data transformation functions
    - JSON template support for structured data formatting
    - Batch processing capabilities

Example usage::

    inserter = InserterArtifact(
        jid="inserter@xmpp.server",
        passwd="password",
        publisher_jid="publisher@xmpp.server",
        host="broker.example.com",
        project_name="my_project"
    )

SubscriptionManagerArtifact
~~~~~~~~~~~~~~~~~~~~~~~~~

Manages subscriptions and handles notifications from the Context Broker:

- **Subscription Features**:
    - Create and manage NGSI-LD subscriptions
    - Monitor specific entity attributes under specific conditions
    - Handle subscription lifecycle (create, update, delete)

- **Notification Management**:
    - Automatic endpoint setup for receiving notifications
    - Customizable notification processing
    - Real-time data updates

Example usage::

    subscription_manager = SubscriptionManagerArtifact(
        jid="subscriber@xmpp.server",
        passwd="password",
        config={
            "entity_type": "WasteContainer",
            "entity_id": "088",
            "watched_attributes": [],
            "q_filter": "fillingLevel>0.7",
            "context": [
                "https://raw.githubusercontent.com/smart-data-models/dataModel.WasteManagement/master/context.jsonld"
            ],
            "delete_all_artefact_subscriptions": true,
            "delete_subscription_identifier": "subs_1",
            "subscription_identifier": "subs_2",
            "delete_only": false
        },
        broker_url="http://broker.example.com:9090"
    )

Installation
-----------

Install via pip::

    pip install spade-fiware-artifacts

Quick Start
----------

1. **Configure Your Environment**

Create a config.json file::

    {
        "XMPP_SERVER": "your.xmpp.server",
        "subscriber_artifact_name": "art_subscriber",
        "broker_port": "http://localhost:9090"
    }

2. **Initialize Artifacts**

.. code-block:: python

    from spade_fiware_artifacts import InserterArtifact, SubscriptionManagerArtifact

    # Set up inserter
    inserter = InserterArtifact(
        jid="inserter@xmpp.server",
        passwd="password",
        publisher_jid="publisher@xmpp.server",
        host="localhost",
        project_name="test_project"
    )

    # Set up subscription manager
    subscription_manager = SubscriptionManagerArtifact(
        jid="subscriber@xmpp.server",
        passwd="password",
        config=subscription_config,
        broker_url="http://localhost:9090"
    )

Use Cases
--------

- IoT Data Management: Handle real-time sensor data
- Smart City Applications: Monitor and manage urban infrastructure
- Industrial IoT: Track manufacturing processes and equipment
- Environmental Monitoring: Collect and process environmental data

Requirements
-----------

- Python 3.7+
- SPADE
- aiohttp
- loguru

Documentation
------------

For detailed documentation, visit our `ReadTheDocs <https://spade-fiware-artifacts.readthedocs.io/en/latest/>`_ page.

Contributing
-----------

We welcome contributions! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

License
-------

This project is licensed under the MIT License - see the LICENSE file for details.

Support
-------

If you have any questions or need support, please:

- Check our documentation
- Open an issue on GitHub
- Contact the maintainers