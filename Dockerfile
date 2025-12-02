# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder
WORKDIR /app

# build-time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# copy requirements, install into /install for later copy
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN python -m pip install --prefix=/install -r /app/requirements.txt

# copy source for inclusion in the final image
COPY . /app

# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# install runtime system packages (cron, tzdata)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron tzdata \
    && rm -rf /var/lib/apt/lists/*

# set timezone to UTC
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime && echo "UTC" > /etc/timezone

# copy installed python packages from the builder
COPY --from=builder /install /usr/local
ENV PATH=/usr/local/bin:$PATH

# copy app and support files
COPY --from=builder /app /app

# create runtime mount points
VOLUME ["/data", "/cron"]

# expose port 8080
EXPOSE 8080

# copy entrypoint
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
