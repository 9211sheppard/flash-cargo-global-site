# Flash Cargo Global analytics rollout

1. Cloudflare: blocked until DNS/hosting can be placed behind Cloudflare; Wix-registered domain cannot change nameservers from this setup.
2. GA4: waiting on real GA4 Measurement ID; add it once available and filter referrers for chatgpt, openai, perplexity, claude, copilot, and gemini.
3. Direct traffic: create a GA4 exploration for landing pages under `/planning/`, `/guides/`, `/resources/`, and `/trust-center/`.
4. Logs: GitHub Pages does not expose raw server logs; use Cloudflare or a hosting move when ready.
5. IndexNow: active; submit sitemap URLs after every deployment.
