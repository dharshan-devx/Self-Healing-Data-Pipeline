FROM apache/airflow:2.8.1

USER root

RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
        openjdk-11-jdk \
        netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

USER airflow

COPY ./airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY ./airflow/dags /opt/airflow/dags
COPY ./spark /opt/spark
COPY ./data_source /opt/data_source
COPY ./great_expectations /opt/great_expectations
FROM apache/airflow:2.8.1

# Switch to root
USER root

# Install Java (Spark needs it) + netcat
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
        default-jdk \
        netcat-openbsd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME dynamically
RUN JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java)))) && \
    echo "JAVA_HOME=$JAVA_HOME" >> /etc/environment

# Switch back to airflow
USER airflow

# Install Python dependencies
COPY ./airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy DAGs, Spark jobs, data source, expectations
COPY ./airflow/dags /opt/airflow/dags
COPY ./spark /opt/spark
COPY ./data_source /opt/data_source
COPY ./great_expectations /opt/great_expectations
