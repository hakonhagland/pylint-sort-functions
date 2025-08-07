"""Click CLI application with decorator exclusion testing."""

import click


# These decorated commands should be excluded from sorting
@click.group()
@click.option("--verbose", is_flag=True, help="Verbose output")
def cli(verbose):
    """Main CLI group."""
    pass


@cli.command()
@click.option("--name", required=True, help="User name")
@click.option("--email", help="User email")
def create_user(name, email):
    """Create a new user."""
    click.echo(f"Created user: {name}")


@cli.command()
@click.argument("user_id", type=int)
def delete_user(user_id):
    """Delete a user."""
    click.echo(f"Deleted user: {user_id}")


@cli.group()
def admin():
    """Admin commands."""
    pass


@admin.command()
def backup():
    """Backup database."""
    click.echo("Backup completed")


# These regular functions should trigger sorting violations
def zebra_validator(value):
    """Validator function out of order."""
    return value.strip()


def alpha_validator(value):
    """Should come before zebra_validator."""
    return value.lower()


def _zebra_helper():
    """Private helper out of order."""
    return "help"


def _alpha_helper():
    """Should come before _zebra_helper."""
    return "help"


class CommandProcessor:
    """Command processor with method sorting issues."""

    def zebra_process(self, cmd):
        """Process method out of order."""
        return cmd

    def alpha_process(self, cmd):
        """Should come before zebra_process."""
        return cmd
