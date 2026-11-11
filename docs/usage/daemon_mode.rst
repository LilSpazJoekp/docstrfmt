#############
 Daemon Mode
#############

docstrfmt provides a daemon mode that runs as an HTTP server, allowing for fast
formatting via HTTP requests. This is particularly useful for editor integration and
high-performance scenarios.

**************
 Installation
**************

To use daemon mode, install docstrfmt with the optional daemon dependencies:

.. code-block:: bash

    pip install "docstrfmt[d]"

For uv and for the development version, see :ref:`installing-with-daemon-support`.

*********************
 Starting the Daemon
*********************

Start the docstrfmt daemon:

.. code-block:: bash

    docstrfmtd

By default, the daemon binds to ``localhost:5219``. You can specify custom host and
port:

.. code-block:: bash

    docstrfmtd --bind-host 0.0.0.0 --bind-port 8080

**********************
 Command Line Options
**********************

.. click:: docstrfmt.server:main
    :prog: docstrfmtd
    :nested: full

******************
 Using the Daemon
******************

HTTP API
========

The daemon provides a simple HTTP API for formatting:

**Endpoint**: ``POST /``

**Request Body**: The reStructuredText content to format (as raw text)

**Headers**:

- ``X-Line-Length``: Optional line length; defaults to 88

**Response**: The formatted content

.. note::

    The daemon formats reStructuredText only. A Python file sent to it is parsed as
    reStructuredText, so its docstrings are not handled the way the ``docstrfmt``
    command handles them. The daemon also ignores ``pyproject.toml``: pass the line
    length in ``X-Line-Length``. Every other option uses its default, except that
    existing section adornments are kept, as with :option:`--preserve-adornments
    <docstrfmt --preserve-adornments>`.

Basic Usage
===========

Format a file using curl:

.. code-block:: bash

    curl http://localhost:5219 --data-binary @myfile.rst

Format with custom line length:

.. code-block:: bash

    curl -H 'X-Line-Length: 72' http://localhost:5219 --data-binary @myfile.rst

Format from stdin:

.. code-block:: bash

    echo "Some reStructuredText content" | curl -fsS http://localhost:5219 --data-binary @/dev/stdin

Python Integration
==================

Use the daemon from Python:

.. code-block:: python

    import requests

    # Format content
    content = "Some reStructuredText content"
    response = requests.post("http://localhost:5219", data=content)
    response.raise_for_status()
    formatted = response.text

    # Format with custom line length
    headers = {"X-Line-Length": "72"}
    response = requests.post("http://localhost:5219", data=content, headers=headers)
    response.raise_for_status()
    formatted = response.text

********************
 Editor Integration
********************

The daemon is particularly useful for editor integration as it avoids the overhead of
starting docstrfmt for each formatting request.

VS Code Extension
=================

Create a VS Code extension that uses the daemon:

.. code-block:: javascript

    const vscode = require('vscode');
    const http = require('http');

    function formatWithDaemon(content, lineLength = 88) {
        return new Promise((resolve, reject) => {
            const options = {
                hostname: 'localhost',
                port: 5219,
                path: '/',
                method: 'POST',
                headers: {
                    'X-Line-Length': lineLength.toString(),
                    'Content-Length': Buffer.byteLength(content)
                }
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    if (res.statusCode === 200) {
                        resolve(data);
                    } else {
                        reject(new Error(data));
                    }
                });
            });

            req.on('error', reject);
            req.write(content);
            req.end();
        });
    }

Vim Integration
===============

Add to your ``.vimrc``:

.. code-block:: vim

    function! DocstrfmtDaemon()
        let content = join(getline(1, '$'), "\n")
        let formatted = system('curl -sS --fail-with-body -H "X-Line-Length: 72" http://localhost:5219 --data-binary @-', content)
        if v:shell_error
            echoerr 'docstrfmt daemon: ' . formatted
            return
        endif
        let lines = split(formatted, "\n")
        call setline(1, lines)
    endfunction

    command! DocstrfmtDaemon call DocstrfmtDaemon()

**********************
 Performance Benefits
**********************

Startup Time
============

The daemon avoids the overhead of:

- Starting the Python interpreter
- Importing all dependencies
- Registering the docutils and Sphinx directives and roles

This makes it much faster for repeated formatting requests.

Concurrent Requests
===================

Requests are handled on a single event loop, and formatting itself is synchronous, so
requests are processed one at a time. A large document delays the requests queued behind
it.

****************
 Error Handling
****************

HTTP Status Codes
=================

The daemon returns one of three HTTP status codes:

- ``200 OK``: Formatting successful; the body is the formatted text
- ``400 Bad Request``: The input is not valid reStructuredText, or the ``X-Line-Length``
  header is not an integer
- ``500 Internal Server Error``: Any other error

Error Response Format
=====================

Error responses are plain text, and the body is the error message. For input that cannot
be parsed, it is the message the ``docstrfmt`` command would print:

.. code-block:: text

    HTTP/1.1 400 Bad Request
    Content-Type: text/plain; charset=utf-8

    ERROR: File "<server_input>", line 3:
    Malformed table.
    Text in column margin in table line 2.

Clients should check the status code before using the response body. With curl, pass
``--fail-with-body`` (curl 7.76 or newer) to get a non-zero exit code and still see the
message; ``-f`` also fails but hides it.

*************************
 Security Considerations
*************************

Network Access
==============

By default, the daemon only accepts connections from localhost. For remote access,
consider:

- Using a reverse proxy (nginx, Apache)
- Implementing authentication
- Using HTTPS with proper certificates

Resource Limits
===============

Consider implementing:

- Request rate limiting
- Maximum request size limits
- Timeout handling
- Memory usage monitoring

***********************
 Production Deployment
***********************

Process Management
==================

Use a process manager like systemd, supervisor, or PM2:

.. code-block:: ini

    [Unit]
    Description=docstrfmt daemon
    After=network.target

    [Service]
    Type=simple
    User=docstrfmt
    ExecStart=/usr/local/bin/docstrfmtd --bind-host 0.0.0.0 --bind-port 5219
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Docker Deployment
=================

Create a Dockerfile:

.. code-block:: dockerfile

    FROM python:3.11-slim

    RUN pip install "docstrfmt[d]"

    EXPOSE 5219

    CMD ["docstrfmtd", "--bind-host", "0.0.0.0", "--bind-port", "5219"]

Monitoring
==========

Monitor the daemon for:

- Response times
- Error rates
- Memory usage
- Request volume

**********
 Examples
**********

Start daemon on custom port:

.. code-block:: bash

    docstrfmtd --bind-port 8080

Format file via daemon:

.. code-block:: bash

    curl http://localhost:5219 --data-binary @documentation.rst

Format with custom line length:

.. code-block:: bash

    curl -H 'X-Line-Length: 72' http://localhost:5219 --data-binary @documentation.rst

Format from stdin:

.. code-block:: bash

    echo "Some content" | curl -fsS http://localhost:5219 --data-binary @/dev/stdin
