#!/bin/bash
# run_udp_test.sh

python3 udp_test.py \
  -p 44445 \
  -q cbid? \
  --loop \
  -l 10 \
  -c compose-cyberbox-A-1 \
  --logfile results.json \
  --logformat json \
  --log-on all \
  --timestamp-format iso
