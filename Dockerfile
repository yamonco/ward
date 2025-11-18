# Ward Security System Docker Image
FROM ubuntu:22.04

LABEL maintainer="yamonco <dev@yamonco.com>"
LABEL description="Ward Security System - Enterprise file system protection"
LABEL version="2.0.0"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV WARD_ROOT=/opt/ward
ENV PATH=$WARD_ROOT:$PATH

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    findutils \
    grep \
    sed \
    gawk \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN pip3 install uv

# Create ward user
RUN useradd -m -s /bin/bash ward

# Create Ward directory
WORKDIR $WARD_ROOT

# Copy Ward system files
COPY .ward/ .ward/
COPY setup-ward.sh ./

# Make scripts executable
RUN chmod +x setup-ward.sh

# Copy Python wrapper
COPY src/ src/
RUN pip3 install -e .

# Set ownership
RUN chown -R ward:ward $WARD_ROOT

# Switch to ward user
USER ward

# Initialize Ward Security
RUN ./setup-ward.sh

# Expose volume for projects
VOLUME ["/workspace"]

# Set working directory for users
WORKDIR /workspace

# Default command
CMD ["ward-shell"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ward-cli status || exit 1