FROM temporalio/server:1.31.2

USER root
COPY dynamicconfig/development-sql.yaml /etc/temporal/config/dynamicconfig/docker.yaml
RUN chmod 0444 /etc/temporal/config/dynamicconfig/docker.yaml

USER 1000:1000
