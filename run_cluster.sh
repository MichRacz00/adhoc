#!/bin/bash

NUM_NODES=15
python3 src/run.py $NUM_NODES topologies/cluster.yaml cluster
#python3 src/util.py $NUM_NODES topologies/election.yaml dolev
docker-compose build
docker-compose up
