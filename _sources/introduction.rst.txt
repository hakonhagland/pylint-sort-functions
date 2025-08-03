Introduction
============

``pylint-sort-functions`` is a PyLint plugin that enforces alphabetical sorting of functions and methods within Python classes and modules.

Features
--------

* **Function Organization**: Enforces alphabetical sorting of functions within modules
* **Method Organization**: Enforces alphabetical sorting of methods within classes
* **Public/Private Separation**: Ensures public functions/methods come before private ones (underscore prefix)
* **Configurable Rules**: Customizable message codes (W9001-W9003) for different violations
* **Clear Error Messages**: Helpful messages indicating exactly what needs to be reordered

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install pylint-sort-functions

Quick Start
-----------

Enable the plugin in your pylint configuration:

.. code-block:: bash

   pylint --load-plugins=pylint_sort_functions your_module.py

Or add to your ``.pylintrc`` file:

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

Message Codes
-------------

The plugin defines these message types:

* **W9001**: ``unsorted-functions`` - Functions not sorted alphabetically within their scope
* **W9002**: ``unsorted-methods`` - Class methods not sorted alphabetically within their scope
* **W9003**: ``mixed-function-visibility`` - Public and private functions not properly separated
