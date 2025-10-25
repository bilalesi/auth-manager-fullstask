#!/bin/bash
set -e  # exit on error
set -u  # exit on undefined variable
set -o pipefail  # exit on pipe failure


KEYCLOAK_HOST=localhost
KEYCLOAK_PORT=8081

echo "Waiting for Keycloak health endpoint..."

while ! </dev/tcp/$KEYCLOAK_HOST/$KEYCLOAK_PORT; do
    echo "Keycloak not ready yet..."
    sleep 5
done

echo "Keycloak is up!"

/opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8081/auth --realm master --user admin --password admin
echo "Server connected"

/opt/keycloak/bin/kcadm.sh update realms/master -s sslRequired=NONE
echo "SSL disabled"

/opt/keycloak/bin/kcadm.sh create users -r SBO -s username=vault.obi -s enabled=true -s email=vault@obi.com -s emailVerified=true
echo "User created"

/opt/keycloak/bin/kcadm.sh set-password -r SBO --username vault.obi --new-password vault
echo "User password set"

