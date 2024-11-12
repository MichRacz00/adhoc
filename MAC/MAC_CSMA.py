import random
import sys
import itertools as it
import pandas as pd

DEBUG = False

def log(line):
    if DEBUG:
        print(line)

class Node:

    def __init__(self, _id, transmission_time, packet_generation_period, initial_offset, p):
        self.id = _id
        self.transmitting = False
        self.transmission_time = transmission_time
        self.pgp = packet_generation_period
        self.backoff = 8
        self.time_till_periodic_packet = initial_offset
        self.time_till_backed_off_packet = None
        self.time_till_transmission_end = 0

        self.p = p

        self.queued_messages = 0

        self.statistics = {
            'successful_packets': 0,
            'total_packets': 0,
        }

    def update_time(self, step, channel_busy):
        # If backoff is over, start transmitting the earliest unsent packet
        if self.time_till_backed_off_packet is not None and self.time_till_backed_off_packet == 0:

            # Models waiting for channel to be idle
            if channel_busy:
                self.time_till_backed_off_packet = 1
            else:
                if self.can_send():
                    log(f"[Node {self.id}] Transmitting backed off packet!")
                    self.start_transmitting()
                    self.time_till_backed_off_packet = None
                else:
                    # Models waiting for packet worst case propagation delay
                    self.time_till_backed_off_packet = 1

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
            if channel_busy:
                self.time_till_backed_off_packet = 1
            else:
                if not self.transmitting and self.time_till_backed_off_packet is None:
                    if self.can_send():
                        log(f"[Node {self.id}] Sending newly generated packet")
                        self.start_transmitting()
                    else:
                        self.time_till_backed_off_packet = 1
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

    def can_send(self):
        ptry = random.random()

        log(f"[Node {self.id}] Generated random number {ptry} < {self.p}: {ptry < self.p}")

        return ptry < self.p

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

        channel_busy = any(filter(lambda n: n.is_transmitting(), self.nodes))

        for n in self.nodes:
            n.update_time(step, channel_busy)

        transmitting_nodes = [n for n in self.nodes if n.is_transmitting()]

        if len(transmitting_nodes) > 1:
            log(f"[Collission] {[n.id for n in transmitting_nodes]} are transmitting at the same time!")

            for n in transmitting_nodes:
                n.stop_transmitting(True)

            return True

        return False

time_steps = int(sys.argv[1])

try:
    if sys.argv[2] == "--debug":
        DEBUG = True
except:
    pass

N = [2, 5, 10, 20, 30, 40, 50, 100]
GEN_PERIOD = [5, 10, 25, 50]
PS = [1]
P = [1, 0.9, 0.75, 0.5, 0.2, 0.1, 0.01, 0.001]

REPS = 5

with open('MAC_results.txt', 'w') as f:

    results = {
        "n": [],
        "gen_period": [],
        "ps": [],
        "p": [],
        "successful": [],
        "total": [],
    }

    for n in range(100):
        results.update({f"successful_{n}": []})
        results.update({f"total_{n}": []})

    for (n, gen_period, ps, p) in it.product(N, GEN_PERIOD, PS, P):

        print(f"Simulator with n={n} gen_period={gen_period} packet_size={ps} p={p}...")
        print(f"Simulator with n={n} gen_period={gen_period} packet_size={ps} p={p}:", file=f)

        print(f"n * p {'>' if n * p >= 1 else '<'} 1")
        print(f"n * p {'>' if n * p >= 1 else '<'} 1", file=f)

        avgs = dict([(i, { 'successful_packets': 0, 'total_packets': 0}) for i in range(n)])

        # Run simulation
        for _ in range(REPS):
            s = Simulator([Node(i, ps, gen_period, 0, p) for i in range(n)], 1)
            s.run(time_steps)

            for i in range(n):
                avgs[i]['successful_packets'] += s.nodes[i].statistics['successful_packets']
                avgs[i]['total_packets'] += s.nodes[i].statistics['total_packets']

        for i in range(n):
            avgs[i]['successful_packets'] /= REPS
            avgs[i]['total_packets'] /= REPS

        successful = sum([a['successful_packets'] for a in avgs.values()])
        total = sum([a['total_packets'] for a in avgs.values()])

        # Add to dataframe results
        for i in range(n):
            results[f'successful_{i}'].append(avgs[i]['successful_packets'])
            results[f'total_{i}'].append(avgs[i]['total_packets'])

        for i in range(n, 100):
            results[f'successful_{i}'].append(None)
            results[f'total_{i}'].append(None)

        results['n'].append(n)
        results['gen_period'].append(gen_period)
        results['ps'].append(ps)
        results['p'].append(p)
        results['successful'].append(successful)
        results['total'].append(total)

        print(f"""[Statistic] Total transmitted packets: {successful}/{total} = {successful / total} channel utilization""", file=f)
        print()
        print(file=f)

    pd.DataFrame(results).to_csv('MAC_results.csv')
