import string
import json
import random
import asyncio

from ipv8.community import CommunitySettings
from ipv8.messaging.payload_dataclass import overwrite_dataclass
from dataclasses import dataclass

from ipv8.types import Peer

from da_types import *

# We are using a custom dataclass implementation
dataclass = overwrite_dataclass(dataclass)

@dataclass(
    msg_id=1
)
class Broadcast:
    origin: int
    path: str    # only hashable types allowed so dictionary converted to string
    message: str

class Dolev(DistributedAlgorithm):

    # messages to start brodcast with
    messages = {0: "Foo!", 1: "Bar.", 2: "Hello, World!"}

    # max bizantine nodes allowed
    f = 1

    # delay of the network (requirenment of assignment)
    delay_lower_bound = 1
    delay_upper_bound = 3

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

        self.empty_path_sent = {}
        self.delivered_self = {}
        self.delivered_neighbours = {}
        self.paths = {}
        self.empty_path = {}

        # initailize internal data structures
        # disjoint for all messages
        for nodes in Dolev.messages:
            message = Dolev.messages[nodes]
            self.empty_path_sent[message] = False
            self.delivered_self[message] = False
            self.delivered_neighbours[message] = set()
            self.paths[message] = []
            self.empty_path[message] = False

        # add message handler for when a message is received
        self.add_message_handler(Broadcast, self.received)

    async def on_start(self):
        # check if this node has a message to brodcast
        if self.node_id in Dolev.messages.keys():
            # fetch message to brodcast
            message = Dolev.messages[self.node_id]

            # send brodcast message to all neighbours
            for peer in list(self.nodes.values()):
                await self.send_with_delay(peer, [], message)

            # deliver brodcast message to self
            self.delivered_self[message] = True
            print(f"Message \"{message}\" has been delivered, this is the source.")

    async def send_with_delay(self, destination, path, message):
        # simulate network delay (requirenment of the assignment)
        await asyncio.sleep(random.uniform(Dolev.delay_lower_bound, Dolev.delay_upper_bound))
        self.ez_send(destination, Broadcast(self.node_id, json.dumps(list(path)), message))

    # check for node disjoint paths
    def ammount_disjoint_paths(self, origin, message):
        disjoint_paths = 0
        # this list is used to record nodes that have a path running over them
        # has to include a dummy value -1, otherwise .update() doesn't work
        traversed_nodes = {-1}
        disjoint = True

        if len(self.paths[message]) < 1:
            return 0

        # check for shortest paths first
        paths_sorted = sorted(self.paths[message], key=len)

        # iterate over all known paths from the origin of the message
        for path in paths_sorted:
            for node in path:
                # if a node has already been used in a diffrent path,
                # this path is not disjoint
                # sinde path also includes destination and origin, ignore them
                if node in traversed_nodes and node != self.node_id and node != origin:
                    disjoint = False
                    break
            # if the path is disjoint, increment counter
            # and update the list of nodes already used
            if disjoint:
                traversed_nodes.update(path)
                disjoint_paths += 1
            disjoint = True
        return disjoint_paths

    @lazy_wrapper(Broadcast)
    async def received(self, peer: Peer, payload: Broadcast) -> None:

        # recover data from the message to a usable format
        origin = payload.origin
        message = payload.message
        path = set(json.loads(payload.path))

        print(f"Received a packet from {origin}, by way of {path}.")

        # MD.3 if empty path received, assume node has delivered the message
        if not path:
            print (f"Neighbour {self.node_id_from_peer(peer)} delivered the message.")
            self.delivered_neighbours[message].add(self.node_id_from_peer(peer))

        # add id of this node to path of the message
        path.add(self.node_id)

        # if this is a new brodcast message
        # initialize the path registry entry for this message
        if message not in self.paths.keys():
            self.paths[message] = []
        # add path traveled by the message to the path registry
        (self.paths[message]).append(path)

        path_to_send = set() # path to be sent in the outgoing brodcast
        propagated_to = [] # record of where the brodcast was sent (for human-readible format)

        # propagate message further
        for peer in list(self.nodes.values()):

            # WIP MD.5
            if self.empty_path[message]: continue;

            # MD.1: Deliver if received directly from the source
            if origin == self.node_id_from_peer(peer) and not self.delivered_self[message]:
                self.delivered_self[message] = True
                print(f"Message \"{message}\" has been delivered directly from source {origin}.")

            # MD.2 & MD.5: Discard paths after delivery, relay only with an empty path
            if self.delivered_self[message]:
                self.paths[message] = []
            else:
                path_to_send = path

            # MD.3: Only relay to neighbors who have not delivered the message
            # MD.4: If empty path received, stop relying to that node
            if self.node_id_from_peer(peer) in self.delivered_neighbours[message]: continue

            # do not send messages backwards (back to the sender)
            if self.node_id_from_peer(peer) in path: continue

            # send the message
            await self.send_with_delay(peer, path_to_send, message)

            # record where the message was sent
            propagated_to.append(self.node_id_from_peer(peer))

            # WIP MD.5
            if self.delivered_self[message] and not path_to_send:
                self.empty_path[message] = True

        # MD.5: if message delivered and empty path sent
        #if self.delivered[message] and not path_to_send:
        #    pass
            #self.stop()

        # check for disjoint vertice paths
        #if self.is_disjoint_path(payload.origin):
        ammount_disjoint_paths = self.ammount_disjoint_paths(origin, message)
        if ammount_disjoint_paths >= Dolev.f + 1:
            if not self.delivered_self[message]:
                self.delivered[message] = True
                print(f"Message \"{message}\" has been delivered from node {origin} via {ammount_disjoint_paths} node-disjoint paths.")

        if len(propagated_to) > 0:
            print(f"Message propagated to {propagated_to}.")
