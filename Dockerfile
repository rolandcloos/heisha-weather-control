ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 \
    py3-pip \
    py3-setuptools \
    py3-wheel \
    py3-numpy \
    py3-pandas \
    py3-scipy \
    py3-scikit-learn \
    tzdata \
    jq \
    && rm -rf /var/cache/apk/*

# Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy data for add-on
COPY run.sh /
COPY app/ /opt/app/

# Make run script executable
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]