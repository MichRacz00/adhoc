# Prerequesits
This implementation requires docker and docker compose plugin.

# Running Test Cases
This protocol can be tested with supplied test cases in
four distinct topologies. Topologies are supplied in the
topologies folder.

Before running each test, selected topology must be copied
into the cluster.yaml file. Additionaly, appropriate
topology must be configured in src/cluster.py file on
line 56. The test should be started by running run_cluster.sh
Allow for up to 30 seconds for messages to arrive at their
destinations.

# Acnowledgments
The framework on which this protocol has been implemented was taken
from the course Distributed Algorithms. We do not take credit for
the implementation of the framework.