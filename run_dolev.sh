
NUM_NODES=6
python3 src/util_communication.py $NUM_NODES topologies/communication.yaml dolev
#python3 src/util.py $NUM_NODES topologies/election.yaml dolev
docker-compose build
docker-compose up
