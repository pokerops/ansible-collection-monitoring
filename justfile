# Run the pokerops-monitoring CLI
install:
    make install

run *args:
    uv --no-managed-python run pokerops-monitoring {{ args }}

# Run all pytest checks
test *args:
    uv --no-managed-python run pytest {{ args }}

# Lint code with ruff
lint *args:
    uv --no-managed-python run ruff check {{ args }} python/src python/tests

# Format code with ruff
format *args:
    uv --no-managed-python run ruff format {{ args }} python/src python/tests

# Type check with pyright
types *args:
    uv --no-managed-python run pyright {{ args }}

# Build the package
build:
    uv --no-managed-python build
