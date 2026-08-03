FROM quay.io/keycloak/keycloak:26.3.2 AS builder

WORKDIR /opt/keycloak
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.3.2

COPY --from=builder --chown=keycloak:keycloak /opt/keycloak/ /opt/keycloak/
