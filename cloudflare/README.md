# iPBotS Cloudflare Worker - Sub Link Proxy

Proxies V2Ray subscription links through Cloudflare to bypass filtering.

## Setup

1. Install Wrangler: `npm install -g wrangler`
2. Login: `wrangler login`
3. Deploy: `cd cloudflare && wrangler deploy`

## Usage

Original sub link: `https://panel.example.com/sub/abc123`
Proxied link: `https://your-worker.workers.dev/sub/{base64(https://panel.example.com)}/abc123`

The bot automatically generates proxied links when `CF_WORKER_URL` is set in .env.
