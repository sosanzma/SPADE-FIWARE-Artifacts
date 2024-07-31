.. highlight:: shell

============
Installation
============


Stable release
--------------

To install SPADE-FIWARE-Artifacts, run this command in your terminal:

.. code-block:: bash

    $ pip install spade-fiware-artifacts

This is the preferred method to install SPADE-FIWARE-Artifacts, as it will always install the most recent stable release.

If you don't have `pip <https://pip.pypa.io>`_ installed, this `Python installation guide <http://docs.python-guide.org/en/latest/starting/installation/>`_ can guide you through the process.

From sources
------------

The sources for SPADE-FIWARE-Artifacts can be downloaded from the `Github repo <https://github.com/sosanzma/SPADE-FIWARE-Artifacts>`_.

You can clone the public repository:

.. code-block:: bash

    $ git clone git://github.com/sosanzma/SPADE-FIWARE-Artifacts

Or download the `tarball <https://github.com/sosanzma/SPADE-FIWARE-Artifacts/tarball/master>`_:

.. code-block:: bash

    $ curl -OJL https://github.com/sosanzma/SPADE-FIWARE-Artifacts/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: bash

    $ python setup.py install

Development setup
-----------------

If you're setting up SPADE-FIWARE-Artifacts for development:

1. Fork the `SPADE-FIWARE-Artifacts repo <https://github.com/sosanzma/SPADE-FIWARE-Artifacts>`_ on GitHub.
2. Clone your fork locally:

.. code-block:: bash

    $ git clone git@github.com:your_name_here/SPADE-FIWARE-Artifacts.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development:

.. code-block:: bash

    $ mkvirtualenv spade-fiware-artifacts
    $ cd spade-fiware-artifacts/
    $ python setup.py develop

4. Create a branch for local development:

.. code-block:: bash

    $ git checkout -b name-of-your-bugfix-or-feature

Now you can make your changes locally.

5. When you're done making changes, check that your changes pass the tests:

.. code-block:: bash

    $ python setup.py test

6. Commit your changes and push your branch to GitHub:

.. code-block:: bash

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.