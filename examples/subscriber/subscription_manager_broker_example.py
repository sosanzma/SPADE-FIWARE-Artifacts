import asyncio
import json
from getpass import getpass

from loguru import logger
from spade.agent import Agent
from spade_artifact import ArtifactMixin
from spade_fiware_artifacts.context_broker_suscription_manager import SubscriptionManagerArtifact
class Agent_notification(ArtifactMixin, Agent):
    def __init__(self, *args, artifact_jid: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.artifact_jid = artifact_jid

    def artifact_callback(self, artifact, payload):
        logger.info(f"Received from {artifact}: {payload}")

    async def setup(self):
        try:
            await asyncio.sleep(2)
            self.presence.subscribe(self.artifact_jid)
            self.presence.set_available()
            await self.artifacts.focus(self.artifact_jid, self.artifact_callback)
            logger.info("Agent ready and listening to the artifact")
        except Exception as e:
            logger.error(f"An error occurred during agent setup: {str(e)}")


async def main():
    """
    Función principal que inicia el artefacto y el agente.
    """
    # Cargar la configuración general
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        logger.error("El archivo config.json no fue encontrado.")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear config.json: {str(e)}")
        return

    # Cargar la configuración de la suscripción
    try:
        with open('payload.json', 'r') as payload_file:
            payload = json.load(payload_file)
    except FileNotFoundError:
        logger.error("El archivo payload.json no fue encontrado.")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear payload.json: {str(e)}")
        return

    XMPP_SERVER = config.get("XMPP_SERVER")
    broker_url = config.get("broker_url")
    subscriber_artifact_name = config.get("subscriber_artifact_name")

    if not all([XMPP_SERVER, broker_url, subscriber_artifact_name]):
        logger.error("Faltan configuraciones en config.json.")
        return

    subscriber_artifact_jid = f"{subscriber_artifact_name}@{XMPP_SERVER}"
    subscriber_artifact_passwd = getpass(prompt="Password for subscriber artifact> ")

    artifact = SubscriptionManagerArtifact(
        jid=subscriber_artifact_jid,
        passwd=subscriber_artifact_passwd,
        config=payload,
        broker_url=broker_url
    )

    agent_jid = f"agent_notification@{XMPP_SERVER}"
    agent_passwd  = getpass(prompt="Password for agent who receives the notification> ")

    try:
        await artifact.start()

        agent = Agent_notification(jid=agent_jid, password=agent_passwd, artifact_jid=subscriber_artifact_jid)
        await agent.start()

        logger.info("Artefacto y agente iniciados correctamente.")

        while True:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Se produjo un error en la función principal: {str(e)}")
    finally:
        await artifact.stop()
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())