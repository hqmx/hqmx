# HQMX - Unified Media Services

This repository is the central hub for the HQMX project, which consolidates several media conversion, downloading, and generation services under a single, unified architecture.

## Unified Architecture (Single EC2)

All HQMX services are hosted on a single AWS EC2 instance, managed via Nginx as a reverse proxy. This approach simplifies deployment, maintenance, and monitoring.

- **Main Domain**: [https://hqmx.net](https://hqmx.net)
- **Services**:
  - `/converter/`
  - `/downloader/`
  - `/calculator/`
  - `/generator/`
- **API Gateway**: `/api/*`

## Deployment

All frontend assets are deployed simultaneously to the EC2 instance using a unified script.

### How to Deploy

To deploy all project frontends to the EC2 server, run the following command from the project root:

```bash
./deploy_all_to_ec2.sh
```

This script will:
1.  Copy the `frontend` directories of `main`, `converter`, `downloader`, `calculator`, and `generator` to `/var/www/hqmx/` on the server.
2.  Deploy `robots.txt` and the sitemap generation script.
3.  Execute the sitemap generator on the server.
4.  Restart Nginx to apply all changes.

For more details on the architecture, refer to `GEMINI.md`.