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
class DataMessage:
    sender: int
    destination: int
    data: str

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
    cluster_heads = []
    messages = []

    topology = "many_ch"

    if topology == "cluster_dense":
        # Cluster heads for the cluster_dense topology
        cluster_heads = [0, 8]
        messages = [
            DataMessage(1, 9, "Testcase RR: 1 to 9"),
            DataMessage(5, 6, "Testcase RG: 5 to 6"),
            DataMessage(4, 8, "Testcase RC: 4 to 8"),
            DataMessage(6, 5, "Testcase GR: 6 to 5"),
            DataMessage(6, 6, "Testcase GG: 6 to 6"),
            DataMessage(6, 8, "Testcase GC: 6 to 8"),
            DataMessage(4, 6, "Testcase CG: 4 to 6"),
            DataMessage(0, 8, "Testcase CR: 0 to 8"),
            DataMessage(0, 4, "Testcase CC: 0 to 4"),
        ]

    elif topology == "cluster_disconnected":
        cluster_heads = [0, 3, 7, 10, 12]
        messages = [
            DataMessage(5, 1, "Testcase RR: 5 to 1"),
            DataMessage(13, 9, "Testcase RG: 13 to 9"),
            DataMessage(11, 12, "Testcase RC: 1 to 12"),
            DataMessage(2, 4, "Testcase GR: 2 to 4"),
            DataMessage(2, 0, "Testcase GC: 2 to 0"),
            DataMessage(9, 12, "Testcase CG: 9 to 12"),
            DataMessage(0, 6, "Testcase CR: 0 to 6"),
            DataMessage(3, 0, "Testcase CC: 3 to 0"),

            DataMessage(0, 7, "This message should not arrive"),
            DataMessage(2, 12, "This message should not arrive"),
            DataMessage(14, 6, "This message should not arrive"),
            DataMessage(2, 6, "This message should arrive"),
        ]

    elif topology == "cluster_string":
        # Cluster heads and messages for the cluster_string topology
        cluster_heads = [0, 3, 6, 9]
        messages = [
            DataMessage(1, 7, "Testcase RR: 1 to 7"),
            DataMessage(1, 8, "Testcase RG: 1 to 8"),
            DataMessage(1, 9, "Testcase RC: 1 to 9"),
            DataMessage(5, 4, "Testcase GR: 5 to 4"),
            DataMessage(8, 2, "Testcase GG: 8 to 7"),
            DataMessage(5, 0, "Testcase GC: 5 to 0"),
            DataMessage(3, 8, "Testcase CG: 3 to 8"),
            DataMessage(3, 10, "Testcase CR: 3 to 10"),
            DataMessage(0, 6, "Testcase CC: 0 to 6"),
        ]

    elif topology == "many_ch":
        # Cluster heads for the many_ch
        cluster_heads = [1, 2, 3, 4, 5]
        messages = [
            DataMessage(0, 5, "Testcase GC: 0 to 5"),
            DataMessage(3, 0, "Testcase CG: 3 to 0"),
            DataMessage(2, 5, "Testcase CC: 2 to 5"),
        ]
        
    else:
        print("\033[31mUnrecognised topology\033[31m")


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
        self.add_message_handler(DataMessage, self.on_data_message)

    async def on_start(self):
        self.is_cluster_head = self.node_id in ClusterHeadAlgorithm.cluster_heads
        self.printing_suffix = f"__ {self.node_id}"
        if self.is_cluster_head:
            self.printing_suffix = f"CH {self.node_id}"
            
        # await asyncio.sleep(random.uniform(1.0, 3.0))
        #self.routing_table[self.node_id] = set([x[0] for x in self.nodes.items()])


        if self.is_cluster_head:
            # Send ping message to determine gateways -> when node receives more than 2 pings it becomes a gateway
            peers = [x for x in self.nodes.items()]
            # print(f"{self.node_id}: I am a cluster head and sending hello to {[id._next_node_id for id in peers]}")
            
            # As a cluster head we want to initialise our routing table with all nodes in our cluster
            self.routing_table[self.node_id] = set([x[0] for x in self.nodes.items()])
            print(f"{self.printing_suffix}: Initial routing table: {self.routing_table}")
            
            for next_peer in peers:
                #await self.send_packet(next_peer[1], ClusterHello(self.node_id))
                self.ez_send(next_peer[1], ClusterHello(self.node_id))
                # self.ez_send(next_peer[1], ClusterHello(self.node_id))

        await asyncio.sleep(random.uniform(8.0, 14.0))

        for message in ClusterHeadAlgorithm.messages:
            if self.node_id is message.sender:
                await asyncio.sleep(random.uniform(0.5, 1.5))
                if self.is_cluster_head:
                    if message.destination in [x[0] for x in self.nodes.items()]:
                    # Destination is in the current cluster, so simply send it to them!
                        id, peer = [x for x in self.nodes.items() if x[0] is message.destination][0]
                        print(f"{self.printing_suffix}: Sending message to {id} destined for {message.destination}")
                        #await self.send_packet(peer, message)
                        self.ez_send(peer, message)
                        continue
                    
                    shouldContinue = False
                    for key_id, value in self.routing_table.items():
                        if message.destination in value:
                            key_peer = [x[1] for x in self.nodes.items() if x[0] is key_id][0]
                            print(f"{self.printing_suffix}: Sending message to {key_id} destined for {message.destination}")
                            #await self.send_packet(key_peer, message)
                            self.ez_send(key_peer, message)
                            shouldContinue = True
                            break
                    
                    if shouldContinue: continue
                    # Uh oh, not found in the routing table?
                    print(f"\033[31m{self.printing_suffix}: Message for {message.destination} could not be send. Routing table: {self.routing_table}\033[31m")
                    
                else:
                    print(f"{self.printing_suffix}: Forwarding message to {self.connected_heads[0][1]} destined for {message.destination}")
                    #await self.send_packet(self.connected_heads[0][0], message)
                    self.ez_send(self.connected_heads[0][0], message)
    
    @message_wrapper(ClusterHello)
    async def on_hello(self, peer: Peer, payload: ClusterHello) -> None:
        if (peer, payload.cluster_head) not in self.connected_heads:
            self.connected_heads.append((peer, payload.cluster_head))

        print(f"{self.printing_suffix}: Received cluster hello from {payload.cluster_head}")
        
        # self.routing_table[self.node_id] = set([x[0] for x in self.nodes.items()])
        # self.routing_table[payload.cluster_head] 

        if len(self.connected_heads) > 1:
            self.is_gateway = True
            self.printing_suffix = f"GW {self.node_id}"
            print(f"{self.printing_suffix}: I have become a GW. My connected heads: {[x[1] for x in self.connected_heads]}")

            # Send a message to all connected heads saying I have become a gateway for them
            for cluster_head_peer, _ in self.connected_heads:
                #await self.send_packet(cluster_head_peer, GatewayAck(self.node_id))
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
            # self.ez_send(gateway_peer, AdvertiseNeighbours(self.node_id, str([x[0] for x in self.nodes.items()])))
            #await self.send_packet(gateway_peer, RoutingUpdate(self.node_id, str(self.routing_table)))
            self.ez_send(gateway_peer, RoutingUpdate(self.node_id, str(self.routing_table)))
            
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

            #await self.send_packete(peer_head, RoutingUpdate(self.node_id, str(self.routing_table)))
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
        
        if payload.sender in self.routing_table and self.routing_table[payload.sender] == new_entry:
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

                #await self.send_packet(head_peer, RoutingUpdate(self.node_id, str(self.routing_table)))
                self.ez_send(head_peer, RoutingUpdate(self.node_id, str(self.routing_table)))
        
        if self.is_cluster_head:
            for gateway_peer, _ in self.connected_gateways:
                if gateway_peer is peer: continue
                
                #await self.send_packet(gateway_peer, RoutingUpdate(self.node_id, str(self.routing_table)))
                self.ez_send(gateway_peer, RoutingUpdate(self.node_id, str(self.routing_table)))

        # for _, next_peer in self.nodes.items():
        #     if next_peer is peer: 
        #         continue

        #     self.ez_send(peer, RoutingUpdate(self.node_id, str(self.routing_table)))
    
    @message_wrapper(DataMessage)
    async def on_data_message(self, _: Peer, payload: DataMessage) -> None:
        if self.node_id is payload.destination:
            # Yaay, we got a message
            print(f"{self.printing_suffix}: Yaay, got a message from {payload.sender}. Data: {payload.data}")
            return
        
        if self.is_cluster_head:
            if payload.destination in [x[0] for x in self.nodes.items()]:
                # Destination is in the current cluster, so simply send it to them!
                id, destination_peer = [x for x in self.nodes.items() if x[0] is payload.destination][0]
                print(f"{self.printing_suffix}: Sending message to {id} destined for {payload.destination}")
                #await self.send_packet(destination_peer, payload)
                self.ez_send(destination_peer, payload)
                return

        for key_id, value in self.routing_table.items():
            if payload.destination in value or payload.destination is key_id:
                key_peer = [x[1] for x in self.nodes.items() if x[0] is key_id][0]
                print(f"{self.printing_suffix}: Forwarding message to {key_id} destined for {payload.destination}")
                #await self.send_packet(key_peer, payload)
                self.ez_send(key_peer, payload)
                return

        # Destination not found, send error back?
        print(f"\033[31m{self.printing_suffix}: Trying to send message, but could not find destination {payload.destination}.\033[31m")

    async def send_packet(self, destination: Peer, payload):
        #await asyncio.sleep(random.uniform(0.5, 1.5))
        self.ez_send(destination, payload)