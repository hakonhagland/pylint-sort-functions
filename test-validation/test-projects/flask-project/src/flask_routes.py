"""Flask application with decorator exclusion testing."""

from flask import Flask

app = Flask(__name__)


# These decorated functions should be excluded from sorting
@app.route("/users/<int:user_id>")
def get_user(user_id):
    """Get specific user - more specific route."""
    return f"User {user_id}"


@app.route("/users")
def list_users():
    """List all users - less specific route."""
    return "All users"


@app.before_request
def before_request():
    """Before request handler."""
    pass


@app.errorhandler(404)
def not_found_handler(error):
    """Handle 404 errors."""
    return "Not found", 404


# These regular functions should trigger sorting violations
def zebra_helper():
    """Helper function out of order."""
    return "zebra"


def alpha_helper():
    """Should come before zebra_helper."""
    return "alpha"


def _private_zebra():
    """Private function out of order."""
    return "private"


def _private_alpha():
    """Should come before _private_zebra."""
    return "private"
