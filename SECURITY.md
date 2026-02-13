# Security Policy

## Supported Versions

Only the latest version on the `main` branch is actively maintained.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly by opening a private GitHub Issue or contacting the maintainer directly. Do not disclose vulnerabilities publicly until a fix is available.

Please include:

- A description of the vulnerability.
- Steps to reproduce it.
- Any potential impact assessment.

We will acknowledge receipt within 48 hours and aim to provide a fix or mitigation as quickly as possible.

## Security Considerations

- **API keys**: Never commit `.env` files or API keys. The `.gitignore` excludes `.env` by default.
- **JWT secrets**: Generate a strong `SECRET_KEY` for production. The default `changethis` value is rejected in production mode.
- **Database credentials**: Change all default passwords before deploying.
- **CORS**: Configure `BACKEND_CORS_ORIGINS` to only allow your frontend domain in production.
