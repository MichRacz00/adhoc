
NUM_NODES=2
python3 src/util.py $NUM_NODES topologies/echo.yaml echo
docker-compose build
docker-compose up
