import string
import json
import random
import asyncio

from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import overwrite_dataclass
from dataclasses import dataclass

from ipv8.types import Peer

from da_types import DistributedAlgorithm, message_wrapper

# We are using a custom dataclass implementation
dataclass = overwrite_dataclass(dataclass)


@dataclass(
    msg_id=1
)  # The value 1 identifies this message and must be unique per community.
class ClusterHello:
    cluster_head: int

@dataclass(
    msg_id=2
)
class Message:
    sender: int
    destination: int

@dataclass(
    msg_id=3
)
class GatewayAck:
    gateway_id: int

class ClusterHeadAlgorithm(DistributedAlgorithm):

    cluster_heads = [1, 3, 7]

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

        self.is_cluster_head = False
        self.is_gateway = False

        self.connected_heads = []
        self.connected_gateways = []

        # Make sure the register the message handlers for each message type
        self.add_message_handler(ClusterHello, self.on_hello)
        self.add_message_handler(GatewayAck, self.on_gateway_ack)

    async def on_start(self):
        self.is_cluster_head = self.node_id in ClusterHeadAlgorithm.cluster_heads

        # await asyncio.sleep(random.uniform(1.0, 3.0))

        if self.is_cluster_head:
            # Send ping message to determine gateways -> when node receives more than 2 pings it becomes a gateway
            peers = [x for x in self.nodes.items()]
            # print(f"{self.node_id}: I am a cluster head and sending hello to {[id._next_node_id for id in peers]}")

            for next_peer in peers:
                self.ez_send(next_peer[1], ClusterHello(self.node_id))

    @message_wrapper(ClusterHello)
    async def on_hello(self, peer: Peer, payload: ClusterHello) -> None:
        if (peer, payload.cluster_head) not in self.connected_heads:
            self.connected_heads.append((peer, payload.cluster_head))

        print(f"{self.node_id}: Received cluster hello from {payload.cluster_head}")

        if len(self.connected_heads) > 1:
            self.is_gateway = True
            print(f"{self.node_id}: I have become a gateway. My connected heads: {[x[1] for x in self.connected_heads]}")

            # Send a message to all connected heads saying I have become a gateway for them
            for cluster_head_peer, _ in self.connected_heads:
                self.ez_send(cluster_head_peer, GatewayAck(self.node_id))

    @message_wrapper(GatewayAck)
    async def on_gateway_ack(self, peer: Peer, payload: GatewayAck) -> None:
        if not self.is_cluster_head: 
            return

        if (peer, payload.gateway_id) not in self.connected_gateways:
            self.connected_gateways.append((peer, payload.gateway_id))
            print(f"{self.node_id}: As a cluster head I am aware of the following gateways: {[x[1] for x in self.connected_gateways]}")

"""
    @message_wrapper(TerminationMessage)
    async def on_terminate(self, peer: Peer, _: TerminationMessage) -> None:
        if self.running:
            _next_node_id, next_peer = [x for x in self.nodes.items() if x[1] != peer][0]
            self.ez_send(next_peer, TerminationMessage())
            self.running = False
            self.stop()

    @message_wrapper(ElectionMessage)
    async def on_message(self, peer: Peer, payload: ElectionMessage) -> None:
        self.running = True
        # Sending it around the ring to the other peer we received it from.
        next_node_id, next_peer = [x for x in self.nodes.items() if x[1] != peer][0]
        print(f'[Node {self.node_id}] Got a message from with elector id: {payload.elector}')

        received_id = payload.elector

        if received_id == self.node_id:
            # We are elected
            print(f'[Node {self.node_id}] we are elected!')
            print(f'[Node {self.node_id}] Sending message to terminate the algorithm!')

            self.ez_send(next_peer, TerminationMessage())
        elif received_id < self.node_id:
            # Send self.node_id along
            self.ez_send(next_peer, ElectionMessage(self.node_id))
        else:  # received_id > self.node_id
            # Send received_id along
            self.ez_send(next_peer, ElectionMessage(received_id))
"""