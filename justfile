# Run the pokerops-monitoring CLI
install:
    make install

run *args:
    uv --no-managed-python run pokerops-monitoring {{ args }}
