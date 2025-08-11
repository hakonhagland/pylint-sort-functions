"""Message definitions for the pylint-sort-functions plugin.

The MESSAGES dict defines all warning/error codes that this PyLint plugin can report.
Each entry creates a new PyLint message that users will see when running PyLint.

Message Structure:
    Key: Message ID (e.g., "W9001")
        - First letter: Severity (W=Warning, E=Error, C=Convention, R=Refactor)
        - Digits: Plugin's unique range (9001-9999 for custom plugins)

    Value: Tuple of (template, symbol, description)
        - Template: Actual message shown to users (supports %s formatting)
        - Symbol: Human-readable name for disabling (e.g., unsorted-functions)
        - Description: Longer explanation for documentation/help

Usage Examples:
    In checker: self.add_message("unsorted-functions", node=node, args=("module",))
    PyLint output: W9001: Functions are not sorted alphabetically in module scope
    (unsorted-functions)
    User disabling: # pylint: disable=unsorted-functions
"""

# Message format: (message_template, message_symbol, message_description)
MESSAGES: dict[str, tuple[str, str, str]] = {
    "W9001": (
        "Functions are not sorted alphabetically in %s scope",
        "unsorted-functions",
        "Functions should be organized alphabetically within their scope "
        "(public functions first, then private functions with underscore prefix)",
    ),
    "W9002": (
        "Methods are not sorted alphabetically in class %s",
        "unsorted-methods",
        "Class methods should be organized alphabetically within their "
        "visibility scope (public methods first, then private methods "
        "with underscore prefix)",
    ),
    "W9003": (
        "Public and private functions are not properly separated in %s",
        "mixed-function-visibility",
        "Public functions (no underscore prefix) should come before private functions "
        "(underscore prefix) with clear separation",
    ),
    "W9004": (
        "Function '%s' should be private (prefix with underscore)",
        "function-should-be-private",
        "Functions that are only used within their defining module should be marked "
        "as private by prefixing their name with an underscore. This rule detects "
        "functions with helper/utility naming patterns (get_, validate_, process_, "
        "helper, etc.) that are called only within the same module. Note: Cannot "
        "detect cross-module usage, so functions used by other modules won't be "
        "flagged (which reduces false positives).",
    ),
    "W9005": (
        "Function '%s' should be public (remove underscore prefix)",
        "function-should-be-public",
        "Functions that are currently marked as private (underscore prefix) but are "
        "used by other modules should be made public by removing the underscore "
        "prefix. This rule detects cross-module imports and usage of private "
        "functions, indicating they are part of the module's public API.",
    ),
    "W9006": (
        "Method '%s' is in wrong section (expected: %s, found: %s)",
        "method-wrong-section",
        "Method appears under an incorrect section header. Methods should be "
        "organized under section headers that match their categorization "
        "(e.g., test methods under '# Test methods', properties under "
        "'# Properties'). Enable section header enforcement with "
        "enforce-section-headers=true.",
    ),
    "W9007": (
        "Missing section header '%s' for methods in category '%s'",
        "missing-section-header",
        "A section header is required for methods in this category, but no "
        "matching header was found. Add the appropriate section header comment "
        "before methods of this type. Enable with require-section-headers=true.",
    ),
    "W9008": (
        "Section header '%s' has no matching methods",
        "empty-section-header",
        "Section header exists but contains no methods underneath. Either add "
        "methods to this section or remove the unnecessary header. Control with "
        "allow-empty-sections configuration option.",
    ),
}
