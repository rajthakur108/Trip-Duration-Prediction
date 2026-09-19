#!/usr/bin/env bash

LOCAL_TAG=`date +"%Y-%m-%d-%H-%M"`

export LOCAL_IMAGE_NAME="ride-duration-service:${LOCAL_TAG}"

# Start Prefect server in background
prefect server start > prefect.log 2>&1 &

# Wait for Prefect server to initialize
sleep 10

docker build \
    -f tests/integration_tests/Dockerfile \
    -t ${LOCAL_IMAGE_NAME} \
    .

docker run -d \
-e PREFECT_API_URL=http://host.docker.internal:4200/api \
--name taxi-service \
${LOCAL_IMAGE_NAME}

sleep 15

docker cp taxi-service:/app/outputs/result_1.csv ./tests/integration_tests/

uv run pytest ./tests/integration_tests/test.py

ERROR_CODE=$?

if [ ${ERROR_CODE} != 0 ]; then
    docker logs --tail 50 taxi-service
fi

docker stop taxi-service
docker rm taxi-service

pkill -f "prefect server start"

EXIT ${ERROR_CODE}
