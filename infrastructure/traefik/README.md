# Traefik

Deployment for running Traefik. To run, first ensure that the `traefik-public` network is created:

```bash
docker network create traefik-public
```

To start the deployment run:

```bash
docker compose up -d
```
