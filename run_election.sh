
NUM_NODES=5
python3 src/util.py $NUM_NODES topologies/election.yaml dolev
docker-compose build
docker-compose up
