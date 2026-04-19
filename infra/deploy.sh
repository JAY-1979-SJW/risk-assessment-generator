#!/bin/bash
set -e

APP_DIR="/home/ubuntu/apps/risk-assessment-app/app"
INFRA_DIR="$APP_DIR/infra"

cd "$APP_DIR"

echo "[1/4] git pull"
git pull --ff-only

echo "[2/4] docker compose up"
cd "$INFRA_DIR"
docker compose --env-file .env up -d --build

echo "[3/4] container status"
docker ps --filter "name=risk-assessment-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "[4/4] health check"
source .env
sleep 3
curl -sf "http://localhost:${API_PORT}/health" && echo " risk-assessment-api OK" || echo " risk-assessment-api FAIL"
curl -sf "http://localhost:${WEB_PORT}/" && echo " risk-assessment-web OK" || echo " risk-assessment-web FAIL"
