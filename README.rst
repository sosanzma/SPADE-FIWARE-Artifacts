SPADE-FIWARE-Artifacts
=======================

.. image:: https://readthedocs.org/projects/spade-fiware-artifacts/badge/?version=latest
    :target: https://spade-fiware-artifacts.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/actions/workflow/status/sosanzma/spade-fiware-artifacts/python-app.yml
        :target: https://github.com/sosanzma/spade-fiware-artifacts/actions
        :alt: Build Status

.. image:: https://coveralls.io/repos/github/sosanzma/SPADE-FIWARE-Artifacts/badge.svg?branch=main
    :target: https://coveralls.io/github/sosanzma/SPADE-FIWARE-Artifacts?branch=main



**SPADE-FIWARE-Artifacts** is a toolkit designed to integrate SPADE (Smart Python Agent Development Environment) with FIWARE. It enables SPADE-based multi-agent systems to interact with FIWARE's context management system, supporting both Orion and Scorpio Context Brokers. The main goal is to facilitate seamless communication and data sharing between these systems.

Artifacts
-----------

Inserter Artifact
-------------------------

The `InserterArtifact` class allows structured communication with FIWARE's Context Brokers, providing the following functionalities:

1. **Flexible Data Processing**

   - Customizable data processor function for transforming data before insertion, outputting data in JSON format to meet payload requirements.
   - Supports multiple data sources, including APIs and databases.

2. **Entity Management**

   - **Intelligent Entity Handling**: Checks if an entity exists and either creates or updates it accordingly.
   - Supports both partial and complete updates for existing entities, with automatic addition of new attributes.

3. **NGSI-LD Support**

   - Fully supports NGSI-LD, managing various attribute types (Properties, GeoProperties, and Relationships) for compatibility with FIWARE.

4. **Asynchronous Operations**

   - Utilizes `asyncio` for non-blocking operations, improving performance when managing multiple requests.

5. **Configurable JSON Templates**

   - Allows customized JSON templates for data structuring and flexible formatting.

6. **Error Handling and Logging**

   - Comprehensive error handling with detailed logging, powered by `loguru`.

Subscription Manager Artifact
-------------------------

The `SubscriptionManagerArtifact` class manages subscriptions to a FIWARE Context Broker and handles notifications with these key features:

1. **Subscription Management**

   - Capable of retrieving, creating, deleting, and managing subscriptions with the Context Broker.

2. **Notification Handling**

   - Processes incoming notifications, updates recent notifications, and provides comprehensive logging.

3. **Port and IP Handling**

   - Retrieves the local IP and finds an available port for establishing communication endpoints.

How It Works
------------

1. **Configuration**

   - Utilizes configuration files (e.g., `config.json`, `json_template.json`, `payload.json`) for setup and customization.

2. **Data Flow**

   - Data is fetched from an external source (API, database, IoT device), processed, and sent to FIWARE's Context Broker by the `InserterArtifact`.

3. **Entity Handling**

   - If an entity already exists, it is updated with new attributes or specific attribute updates. If not, a new entity is created.

4. **XMPP Communication**

   - SPADE’s artifact system is used for data exchange between the data source and the inserter.

5. **Subscription Notifications**

   - The `SubscriptionManagerArtifact` receives and manages notifications based on active subscriptions.

Compatibility
-------------

This toolkit is compatible with both Orion and Scorpio Context Brokers, supporting interaction with NGSI-LD API implementations.

Documentation
-------------

For detailed documentation, please visit the `ReadTheDocs <https://spade-fiware-artifacts.readthedocs.io/en/latest/>`_.

Contributing
------------

Contributions are welcome! Feel free to submit a Pull Request.

License
-------

This project is licensed under the MIT License.
