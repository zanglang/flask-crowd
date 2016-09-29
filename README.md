# Crowd Authentication Microservice

## Introduction

This is a simple authentication microservice written with the Python Flask framework that is designed to be used with Nginx's `auth_request` module.

## Example

Start the service with:

    python server.py [--host=<IP>] [--port=9000] [-d|--debug]

Example Nginx configuration block:

    server {
        location /protected {
            # root /var/www/protected;
            # proxy_pass http://protected_server;
            auth_request /auth;
            error_page 401 = /auth/redirect;
        }

        location /auth {
            internal;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_pass http://flask-crowd-server:9000;
        }

        location /auth/redirect {
            return 301 /login?next=$scheme://$http_host$request_uri;
        }

        location /login {
            proxy_pass http://flask-crowd-server:9000;
        }
    }

## Dependencies

- Flask (https://pypi.python.org/pypi/Flask/0.11.1)
- python-crowd (https://pypi.python.org/pypi/Crowd/1.0.1)
