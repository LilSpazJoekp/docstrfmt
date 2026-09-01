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

.. option:: -h, --bind-host HOST

    Host to bind the server to.

    Default: ``localhost``

.. option:: -p, --bind-port PORT

    Port to bind the server to.

    Default: ``5219``

******************
 Using the Daemon
******************

HTTP API
========

The daemon provides a simple HTTP API for formatting:

**Endpoint**: ``POST /``

**Request Body**: The content to format (as raw text)

**Headers**:

- ``X-Line-Length``: Optional line length override

**Response**: The formatted content

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
    formatted = response.text

    # Format with custom line length
    headers = {"X-Line-Length": "72"}
    response = requests.post("http://localhost:5219", data=content, headers=headers)
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
                res.on('end', () => resolve(data));
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
        let formatted = system('curl -s -H "X-Line-Length: 72" http://localhost:5219 --data-binary @-', content)
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
- Parsing configuration
- Initializing formatters

This makes it much faster for repeated formatting requests.

Memory Usage
============

The daemon keeps formatters in memory, reducing the overhead of repeated initialization.

Concurrent Requests
===================

The daemon can handle multiple concurrent requests efficiently.

****************
 Error Handling
****************

HTTP Status Codes
=================

The daemon returns appropriate HTTP status codes:

- ``200 OK``: Formatting successful
- ``400 Bad Request``: Invalid request
- ``500 Internal Server Error``: Formatting error

Error Response Format
=====================

Errors are returned as plain-text HTTP responses. The response body is empty; the
error message is placed in the HTTP status reason line. For example, a malformed
request produces a ``400`` response whose reason is the underlying parser message:

.. code-block:: text

    HTTP/1.1 400 <docutils system message text>

Clients should read the status code and reason phrase to surface errors.

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
