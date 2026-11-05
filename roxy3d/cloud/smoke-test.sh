#!/usr/bin/env bash
# Cloud smoke test of cloud-render.sh's network-volume path, including the lost-pod fetch (TEST_FETCH=1).
# A wider GPU list than a full run: any card that renders the smoke will do.
cd "$(dirname "$0")"
TEST_FETCH=1 GPUS="NVIDIA GeForce RTX 5090,NVIDIA GeForce RTX 4090,NVIDIA L40S,NVIDIA RTX PRO 4500 Blackwell Server Edition,NVIDIA A40,NVIDIA RTX A6000" bash cloud-render.sh smoke
echo "smoke test finished (exit $?)"
