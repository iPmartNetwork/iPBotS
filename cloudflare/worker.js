/**
 * iPBotS - Cloudflare Worker for Subscription Links
 * Proxies subscription URLs through Cloudflare to bypass filtering
 * 
 * Deploy: wrangler deploy
 * Usage: https://your-worker.workers.dev/sub/{client_id}
 * 
 * © iPmart Network
 */

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Health check
    if (path === '/health') {
      return new Response(JSON.stringify({ status: 'ok', service: 'iPBotS Sub Proxy' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Sub link proxy: /sub/{panel_host_base64}/{client_id}
    if (path.startsWith('/sub/')) {
      const parts = path.replace('/sub/', '').split('/');
      if (parts.length < 2) {
        return new Response('Invalid path', { status: 400 });
      }

      const panelHostB64 = parts[0];
      const clientId = parts.slice(1).join('/');

      try {
        const panelHost = atob(panelHostB64);
        const subUrl = `${panelHost}/sub/${clientId}`;

        const response = await fetch(subUrl, {
          headers: {
            'User-Agent': request.headers.get('User-Agent') || 'v2ray',
          },
        });

        const body = await response.text();

        return new Response(body, {
          status: response.status,
          headers: {
            'Content-Type': response.headers.get('Content-Type') || 'text/plain',
            'Cache-Control': 'no-cache, no-store',
            'Access-Control-Allow-Origin': '*',
          },
        });
      } catch (e) {
        return new Response('Error: ' + e.message, { status: 500 });
      }
    }

    return new Response('iPBotS Sub Proxy - © iPmart Network', { status: 200 });
  },
};
