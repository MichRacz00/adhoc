# Test cases
Five test cases have been designed to present the correct operation
of the Dolev's algorithm and its implementation.

## Test 1
This test presents a basic operation of Dolev's algorithm. Topology
presented in the Assignment (Figure 1) is used. The message will
be received 10 times - the number of nodes in the network.

### Setup
To run the demonstration execute run_dolev.sh shell script.

## Test 2
This test used the same topology, albeit with a byzantine node.
The byzantine node will drop the message. Since this is 3-connected
topology, (by Manger's theorem) we will be able to realize
reliable communication.

Observe that the message will be delivered to all nodes,
without replication.

### Setup
uncoment lines 31-32 in dolev.py
execute shell script run_dolev.sh
if running other tests, comment lines 31-32 in dolev.py

## Test 3
This test shows that if there are more than f byzantine nodes in
the system, the reliable communication will break. In this scenario
we have two bizantine nodes, each one of them altering the content
of the message. Two bizantine nodes suffice to mislead a subset
of nodes to deliver the wrong message.

### Setup
uncomment lines 35-36 in dolev.py
execute shell script run_dolev.sh
if running other tests, comment lines 35-36 in dolev.py

## Test 4
This test runs in a full connected graph with 6 nodes. Four nodes are bizantine.
The message will be delivered correctly to all nodes.

### Setup
uncomment lines 39-40 in dolev.py
execute shell script run_connected.sh
if running other tests, comment lines 39-40 in dolev.py

## Test 5
This test runs in a ring topology with 5 nodes. The broadcast message
will only be delivered to a subset of nodes. Even with no bizantine nodes,
each node must receive the message from at least 3 disjoint paths.
Some messages will be delivered thanks to rules developed by Bonomi et al.

### Setup
execute shell script run_election.sh
