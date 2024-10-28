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

@dataclass(
    msg_id=4
)
class AdvertiseNeighbours:
    cluster_head: int
    neighbours: str

@dataclass(
    msg_id=5
)
class RoutingUpdate:
    sender: int
    routing_table: str

class ClusterHeadAlgorithm(DistributedAlgorithm):

    cluster_heads = [1, 3, 7]

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

        self.printing_suffix = ""
        self.is_cluster_head = False
        self.is_gateway = False

        self.connected_heads = []
        self.connected_gateways = []

        self.routing_table = {}

        # Make sure the register the message handlers for each message type
        self.add_message_handler(ClusterHello, self.on_hello)
        self.add_message_handler(GatewayAck, self.on_gateway_ack)
        self.add_message_handler(AdvertiseNeighbours, self.on_advertise_neighbours)
        self.add_message_handler(RoutingUpdate, self.on_routing_update)

    async def on_start(self):
        self.is_cluster_head = self.node_id in ClusterHeadAlgorithm.cluster_heads
        self.printing_suffix = f"__ {self.node_id}"
        if self.is_cluster_head:
            self.printing_suffix = f"CH {self.node_id}"
            
        # await asyncio.sleep(random.uniform(1.0, 3.0))

        if self.is_cluster_head:
            # Send ping message to determine gateways -> when node receives more than 2 pings it becomes a gateway
            peers = [x for x in self.nodes.items()]
            # print(f"{self.node_id}: I am a cluster head and sending hello to {[id._next_node_id for id in peers]}")

            self.routing_table[self.node_id] = set([x[0] for x in self.nodes.items()])
            print(f"{self.printing_suffix}: Initial routing table: {self.routing_table}")
            for next_peer in peers:
                self.ez_send(next_peer[1], ClusterHello(self.node_id))

    @message_wrapper(ClusterHello)
    async def on_hello(self, peer: Peer, payload: ClusterHello) -> None:
        if (peer, payload.cluster_head) not in self.connected_heads:
            self.connected_heads.append((peer, payload.cluster_head))

        print(f"{self.printing_suffix}: Received cluster hello from {payload.cluster_head}")

        if len(self.connected_heads) > 1:
            self.is_gateway = True
            self.printing_suffix = f"GW {self.node_id}"
            print(f"{self.printing_suffix}: I have become a GW. My connected heads: {[x[1] for x in self.connected_heads]}")

            # Send a message to all connected heads saying I have become a gateway for them
            for cluster_head_peer, _ in self.connected_heads:
                self.ez_send(cluster_head_peer, GatewayAck(self.node_id))

    @message_wrapper(GatewayAck)
    async def on_gateway_ack(self, peer: Peer, payload: GatewayAck) -> None:
        if not self.is_cluster_head: 
            print(f"{self.printing_suffix}: I'm not a cluster head, but for some reason I got a GW ACK message from {payload.gateway_id}...")
            return

        if (peer, payload.gateway_id) not in self.connected_gateways:
            self.connected_gateways.append((peer, payload.gateway_id))
            print(f"{self.printing_suffix}: Gateways: {[x[1] for x in self.connected_gateways]}")

        # As a cluster head we want to send a message to all gateways informing them of all connected nodes
        for gateway_peer, _ in self.connected_gateways:
            self.ez_send(gateway_peer, AdvertiseNeighbours(self.node_id, str([x[0] for x in self.nodes.items()])))
            
    @message_wrapper(AdvertiseNeighbours)
    async def on_advertise_neighbours(self, peer: Peer, payload: AdvertiseNeighbours) -> None:
        if not self.is_gateway:
            print(f"{self.printing_suffix}: I'm not a GW, but somehow I got a AN message from {payload.sender}...")
            return

        #print(f"{self.node_id}: Received AN message from: {payload.cluster_head}, with: {payload.neighbours}")

        # Update routing table

        if payload.cluster_head not in self.routing_table:
            self.routing_table[payload.cluster_head] = set(eval(payload.neighbours))
        else:

            self.routing_table[payload.cluster_head].update(eval(payload.neighbours))

        print(f"{self.printing_suffix}: AN message from {payload.cluster_head}. Updated routing table: {self.routing_table}")

        # Send routing update to all connected heads, except for the one from which you received the AN message
        for peer_head, id_head in self.connected_heads:
            if peer_head is peer: 
                continue

            self.ez_send(peer_head, RoutingUpdate(self.node_id, str(self.routing_table)))

    @message_wrapper(RoutingUpdate)
    async def on_routing_update(self, peer: Peer, payload: RoutingUpdate) -> None:
        if not self.is_cluster_head and not self.is_gateway:
            return

        incoming_rt = eval(payload.routing_table)
        
        incoming_rt.pop(self.node_id, None)
        # print(f"{self.printing_suffix}: RU from {payload.sender}, RT before update: {self.routing_table}")
        
        new_entry = set()
        new_entry.add(payload.sender)
        for key, values in incoming_rt.items():
            new_entry.add(key)
            # print(f"{self.printing_suffix}: RU from {payload.sender}, TEST {key}: {values}")
            new_entry.update(values)
        
        if payload.sender in self.routing_table and self.routing_table[payload.sender] is new_entry:
            # We already got the latest information!
            print(f"{self.printing_suffix}: RU from {payload.sender}, but new entry is the same! So, ignoring.")
            return

        self.routing_table[payload.sender] = new_entry
        # self.routing_table = {**self.routing_table, **incoming_rt}
        print(f"{self.printing_suffix}: RU from {payload.sender}, adding to RT: {new_entry}, after update: {self.routing_table}")

        # For all gateways send another advertise neighbours message
        #print(f"{self.printing_suffix}: Sending routing table: {str(self.routing_table)} to {[x[1] for x in self.connected_gateways]}")
        # print(f"{self.printing_suffix}: RU from {payload.sender}, Known gateways: {self.connected_gateways}")
        # for gateway_peer, _ in self.connected_gateways:

        if self.is_gateway:
            for head_peer, _ in self.connected_heads:
                if head_peer is peer: continue

                self.ez_send(head_peer, RoutingUpdate(self.node_id, str(self.routing_table)))
        
        if self.is_cluster_head:
            for gateway_peer, _ in self.connected_gateways:
                if gateway_peer is peer: continue
                
                self.ez_send(gateway_peer, RoutingUpdate(self.node_id, str(self.routing_table)))

        # for _, next_peer in self.nodes.items():
        #     if next_peer is peer: 
        #         continue

        #     self.ez_send(peer, RoutingUpdate(self.node_id, str(self.routing_table)))