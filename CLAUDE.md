# Development Guidelines for Claude

## CLI Command Pattern

When adding new CLI commands to this project, follow the **hybrid pattern** demonstrated in `src/pokerops_monitoring/ntp.py`.

### Pattern Structure

Each feature module should contain:

1. **A typer app instance** for the command group
2. **Thin CLI wrapper functions** with typer decorators that handle CLI concerns
3. **Pure business logic functions** with no CLI dependencies

### Example

```python
import typer

app = typer.Typer(help="Feature description")


@app.command("command-name")
def feature_command_cmd(
    param: str = typer.Option(..., help="Parameter description"),
) -> None:
    """CLI wrapper - handles typer integration."""
    return feature_command(param)


def feature_command(param: str):
    """Pure business logic - no typer dependencies."""
    # Implementation here
    pass
```

### Benefits of This Pattern

1. **Modularity** - Each feature module owns its CLI structure
2. **Reusability** - Business logic functions can be called from:
   - Other Python code
   - Tests
   - Ansible plugins
   - Other CLI commands
3. **Scalability** - New commands only require editing their feature module
4. **Clean separation** - CLI infrastructure separate from business logic
5. **Easy testing** - Test business logic without CLI/typer mocking

### Integrating with Main CLI

In `src/pokerops_monitoring/cli.py`, simply import and register the feature app:

```python
from pokerops_monitoring.feature import app as feature_app

app.add_typer(feature_app, name="feature")
```

### Why This Pattern?

This hybrid approach combines:
- The scalability of modular CLI structure (user's approach)
- The clean separation of concerns (initial approach)
- The reusability needed for Ansible integration

Continue this pattern for all future commands.
