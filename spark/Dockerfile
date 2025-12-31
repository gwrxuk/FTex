FROM bitnami/spark:3.5

USER root

# Install additional Python packages
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    scikit-learn \
    networkx \
    py4j \
    pyarrow

# Copy job files
COPY jobs /opt/spark/jobs

# Set permissions
RUN chmod -R 755 /opt/spark/jobs

USER 1001

ENTRYPOINT ["/opt/bitnami/scripts/spark/entrypoint.sh"]
CMD ["/opt/bitnami/scripts/spark/run.sh"]

