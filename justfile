GIT_BRANCH := `git rev-parse --abbrev-ref HEAD`

install:
  @make install

configure:
  @sed -iE 's#\(monitoring_script_repo_version:\).*#\1 "{{GIT_BRANCH}}"#' roles/monitoring/defaults/main.yml

run *args:
  @uv --no-managed-python run pokerops-monitoring {{ args }}

# Run all pytest checks
test *args:
  @uv --no-managed-python run pytest {{ args }}

# Lint code with ruff
lint *args:
  @uv --no-managed-python run ruff check {{ args }} python/src python/tests

# Format code with ruff
format *args:
  @uv --no-managed-python run ruff format {{ args }} python/src python/tests

# Type check with pyright
types *args:
  @uv --no-managed-python run pyright {{ args }}

# Build the package
build:
  @uv --no-managed-python build

