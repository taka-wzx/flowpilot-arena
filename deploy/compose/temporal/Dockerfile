FROM temporalio/admin-tools:1.31.2

USER root
COPY setup-postgres.sh /opt/flowpilot-temporal/setup-postgres.sh
COPY create-namespace.sh /opt/flowpilot-temporal/create-namespace.sh
RUN chmod 0555 /opt/flowpilot-temporal/setup-postgres.sh \
    /opt/flowpilot-temporal/create-namespace.sh

USER 1000:1000
