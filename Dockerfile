FROM python:3.15-slim-trixie
WORKDIR /app
COPY pyproject.toml README.md ./
COPY wyoming_halogen ./wyoming_halogen
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home wyoming-halogen
USER wyoming-halogen
EXPOSE 10300
ENTRYPOINT ["wyoming-halogen"]
CMD ["--uri", "tcp://0.0.0.0:10300"]
