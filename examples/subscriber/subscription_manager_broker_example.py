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

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    XMPP_SERVER = config["XMPP_SERVER"]
    broker_port = config["broker_port"]
    subscriber_artifact_name = config["publisher_artifact_name"]
    subscriber_artifact_jid = f"{subscriber_artifact_name}@{XMPP_SERVER}"
    subscriber_artifact_passwd = getpass(prompt="Password for publisher artifact> ")

    artifact = SubscriptionManagerArtifact(subscriber_artifact_jid, subscriber_artifact_passwd, broker_port=broker_port)

    agent_jid = f"agent_notification@{XMPP_SERVER}"
    agent_passwd  = getpass(prompt="Password for agent who receives the notification> ")
    try:
        await artifact.start()

        agent = Agent_notification(jid=agent_jid, password=agent_passwd, artifact_jid=subscriber_artifact_jid)
        await agent.start()
        await artifact.join()
        await artifact.stop()
        await agent.stop()
    except Exception as e:
        logger.error(f"An error occurred in the main function: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())