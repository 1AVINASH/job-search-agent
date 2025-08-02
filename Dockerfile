FROM python:3.13-slim

WORKDIR /app

# COPY Pipfile* ./
RUN pip install uv

# Copy Pipfile first to leverage Docker caching.
# If Pipfile changes, this layer and subsequent layers will be rebuilt.
COPY pyproject.toml uv.lock ./

# IMPORTANT: Remove Pipfile.lock *if it exists in the build context*
# This forces pipenv to resolve dependencies *only* from Pipfile
# and then generate a new Pipfile.lock based on the current Pipfile.
# The `--system` flag installs dependencies into the system's Python environment,
# which is typical and recommended for Docker images.
# The `--deploy` flag ensures that the Pipfile.lock (which will be generated here)
# is consistent with the Pipfile and the installed dependencies.
RUN uv venv && uv sync

COPY . .

CMD ["uv", "run", "main.py"]