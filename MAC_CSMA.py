import random
import sys

DEBUG = False

def log(line):
    if DEBUG:
        print(line)

class Node:

    def __init__(self, _id, transmission_time, packet_generation_period, initial_offset):
        self.id = _id
        self.transmitting = False
        self.transmission_time = transmission_time
        self.pgp = packet_generation_period
        self.backoff = 8
        self.time_till_periodic_packet = initial_offset
        self.time_till_backed_off_packet = None
        self.time_till_transmission_end = 0

        self.queued_messages = 0

        self.statistics = {
            'successful_packets': 0,
            'total_packets': 0,
        }

    def update_time(self, step):
        # If backoff is over, start transmitting the earliest unsent packet
        if self.time_till_backed_off_packet is not None and self.time_till_backed_off_packet == 0:
            log(f"[Node {self.id}] Transmitting backed off packet!")
            self.start_transmitting()
            self.time_till_backed_off_packet = None

        # Successful transmission
        if self.transmitting and self.time_till_transmission_end == 0:
            log(f"[Node {self.id}] Successful transmission")
            self.queued_messages -= 1
            self.stop_transmitting(False)

            if self.queued_messages > 0:
                log(f"[Node {self.id}] Sending next queued packet immediately!")
                self.start_transmitting()

        # Generate a new packet
        if self.time_till_periodic_packet == 0:
            self.time_till_periodic_packet = self.pgp
            self.queued_messages += 1

            self.statistics['total_packets'] += 1

            # If currently backing off, dont try to send yet
            if not self.transmitting and self.time_till_backed_off_packet is None:
                log(f"[Node {self.id}] Sending newly generated packet")
                self.start_transmitting()
            else:
                log(f"[Node {self.id}] Queueing newly generated packet ...")


        if self.transmitting:
            self.time_till_transmission_end -= step

        if self.time_till_backed_off_packet is not None:
            self.time_till_backed_off_packet -= step

        self.time_till_periodic_packet -= step

    def start_transmitting(self):
        self.transmitting = True
        self.time_till_transmission_end = self.transmission_time

    def stop_transmitting(self, conflict):
        self.transmitting = False

        if conflict:
            self.time_till_backed_off_packet = random.randint(0, self.backoff)
            self.backoff = min(self.backoff * 2, 256)

            log(f"[Node {self.id}] Backing off for {self.time_till_backed_off_packet}")
            log(f"[Node {self.id}] Increased backoff to {self.backoff}")
        else:
            self.backoff = max(self.backoff // 2, 8)
            self.statistics['successful_packets'] += 1

            log(f"[Node {self.id}] Decreased backoff to {self.backoff}")

    def is_transmitting(self):
        return self.transmitting

class Simulator:

    def __init__(self, nodes: list[Node], step):
        self.nodes = nodes
        self.time = 0
        self.time_step = step

        self.state_dump = []

    def run(self, iterations):
        for i in range(iterations):
            log(f"[Time] {i * self.time_step}")
            self.step(self.time_step)

    def step(self, step):
        for n in self.nodes:
            n.update_time(step)

        transmitting_nodes = [n for n in self.nodes if n.is_transmitting()]

        if len(transmitting_nodes) > 1:
            log(f"[Collission] {[n.id for n in transmitting_nodes]} are transmitting at the same time!")

            for n in transmitting_nodes:
                n.stop_transmitting(True)

            return True

        return False

    def show_statistics(self):
        for n in self.nodes:
            print(f'[Statistic][Node {n.id}] Successfully transmitted packets: {n.statistics['successful_packets']}/{n.statistics['total_packets']}')

time_steps = int(sys.argv[1])

try:
    if sys.argv[2] == "--debug":
        DEBUG = True
except:
    pass

runs = dict()

for packet_size in range(1, 11):
    s = Simulator([
        Node(0, packet_size, 20, 0),
        Node(1, packet_size, 20, 0),
        Node(2, packet_size, 20, 0),
        Node(3, packet_size, 20, 0),
        Node(4, packet_size, 20, 0),
    ], 1)

    s.run(time_steps)

    runs[packet_size] = s

for (ps, s) in runs.items():
    print(f"Simulator with packet size {ps}:")
    s.show_statistics()