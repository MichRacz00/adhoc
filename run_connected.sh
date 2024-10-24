
NUM_NODES=6
python3 src/util_connected.py $NUM_NODES topologies/connected.yaml dolev
docker-compose build
docker-compose up
