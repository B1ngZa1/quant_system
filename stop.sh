#!/bin/bash
echo "Stopping Quant System..."
# compose down stops containers and releases their host-port bindings.
# (Deliberately no taskkill on 3000/8000: on Docker Desktop those ports are
# held by com.docker.backend / vpnkit, and kill -9 crashes Docker Desktop itself.)
docker compose down 2>/dev/null
echo "Stopped."
