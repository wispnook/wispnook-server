#!/usr/bin/env bash
set -euo pipefail

IFS=',' read -ra TOPICS <<< "${KAFKA_TOPICS}"

for topic in "${TOPICS[@]}"; do
  echo "Creating topic ${topic}"
  kafka-topics --create --if-not-exists --topic "${topic}" --bootstrap-server "${KAFKA_BROKER}" --replication-factor 1 --partitions 3
  kafka-configs --alter --topic "${topic}" --bootstrap-server "${KAFKA_BROKER}" --add-config cleanup.policy=delete
  done
