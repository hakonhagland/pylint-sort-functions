"""Django views with decorator exclusion testing."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# These decorated views should be excluded from sorting
@login_required
@require_http_methods(["GET", "POST"])
def user_profile(request):
    """User profile view."""
    return HttpResponse("Profile")


@csrf_exempt
@require_http_methods(["POST"])
def api_endpoint(request):
    """API endpoint view."""
    return HttpResponse("API")


@login_required
def dashboard(request):
    """Dashboard view - should come before user_profile alphabetically."""
    return HttpResponse("Dashboard")


# These regular functions should trigger sorting violations
def zebra_utility():
    """Utility function out of order."""
    return "zebra"


def alpha_utility():
    """Should come before zebra_utility."""
    return "alpha"


def _zebra_private():
    """Private function out of order."""
    return "private"


def _alpha_private():
    """Should come before _zebra_private."""
    return "private"


class ViewMixin:
    """Class with method sorting issues."""

    def zebra_method(self):
        """Method out of order."""
        pass

    def alpha_method(self):
        """Should come before zebra_method."""
        pass
