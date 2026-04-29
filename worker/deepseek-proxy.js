// Cloudflare Worker proxy for Solar Oracle Walkman DeepSeek mode.
// Deploy:
//   wrangler secret put DEEPSEEK_API_KEY
//   wrangler deploy

const DEFAULT_ALLOWED_ORIGINS = [
  "https://weiweiweiopen.github.io",
  "http://localhost:8000",
  "http://127.0.0.1:8000",
];
const MODEL_BY_MODE = {
  chat: "deepseek-chat",
  reasoner: "deepseek-reasoner",
};
const MAX_BODY_BYTES = 200 * 1024;
const MAX_MESSAGES = 12;
const MAX_CONTENT_CHARS = 16000;
const MAX_TOKENS = 1200;
const DEFAULT_MAX_TOKENS = 900;
const RATE_LIMIT_WINDOW_MS = 60 * 1000;
const RATE_LIMIT_MAX = 30;

const rateBuckets = new Map();

export default {
  async fetch(request, env = {}) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const corsHeaders = buildCorsHeaders(origin, env);

    if (!corsHeaders) return jsonResponse({ error: "Origin not allowed." }, 403);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
    if (url.pathname !== "/chat") return jsonResponse({ error: "Endpoint not found." }, 404, corsHeaders);
    if (request.method !== "POST") return jsonResponse({ error: "Method not allowed." }, 405, corsHeaders);

    if (!env.DEEPSEEK_API_KEY) {
      return jsonResponse({ error: "DeepSeek API key is not configured on the serverless proxy." }, 500, corsHeaders);
    }

    const rateResult = checkRateLimit(request);
    if (!rateResult.allowed) return jsonResponse({ error: "Rate limit exceeded. Please try again later." }, 429, corsHeaders);

    const contentLength = Number(request.headers.get("content-length") || 0);
    if (contentLength > MAX_BODY_BYTES) return jsonResponse({ error: "Request body too large." }, 413, corsHeaders);

    let text;
    try {
      text = await request.text();
    } catch (_error) {
      return jsonResponse({ error: "Could not read request body." }, 400, corsHeaders);
    }

    if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) {
      return jsonResponse({ error: "Request body too large." }, 413, corsHeaders);
    }

    let payload;
    try {
      payload = JSON.parse(text);
    } catch (_error) {
      return jsonResponse({ error: "Invalid JSON body." }, 400, corsHeaders);
    }

    const validation = validatePayload(payload);
    if (!validation.ok) return jsonResponse({ error: validation.error }, 400, corsHeaders);

    const model = MODEL_BY_MODE[payload.mode];
    const maxTokens = Math.min(Number(payload.max_tokens || DEFAULT_MAX_TOKENS), MAX_TOKENS);

    let upstream;
    try {
      upstream = await fetch("https://api.deepseek.com/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.DEEPSEEK_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model,
          messages: payload.messages,
          temperature: 0.2,
          max_tokens: maxTokens,
          stream: false,
        }),
      });
    } catch (_error) {
      return jsonResponse({ error: "DeepSeek request failed." }, 503, corsHeaders);
    }

    if (!upstream.ok) {
      return jsonResponse({ error: safeUpstreamMessage(upstream.status) }, upstream.status === 429 ? 429 : 503, corsHeaders);
    }

    let result;
    try {
      result = await upstream.json();
    } catch (_error) {
      return jsonResponse({ error: "DeepSeek returned an unreadable response." }, 502, corsHeaders);
    }

    return jsonResponse({
      content: result.choices?.[0]?.message?.content || "",
      model,
      usage: result.usage || null,
    }, 200, corsHeaders);
  },
};

function buildCorsHeaders(origin, env) {
  const allowed = String(env.ALLOWED_ORIGINS || DEFAULT_ALLOWED_ORIGINS.join(","))
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  if (!allowed.includes(origin)) return null;
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function validatePayload(payload) {
  if (!payload || typeof payload !== "object") return { ok: false, error: "Request body must be an object." };
  if (!Object.prototype.hasOwnProperty.call(MODEL_BY_MODE, payload.mode)) return { ok: false, error: "Model mode is not allowed." };
  if (!Array.isArray(payload.messages)) return { ok: false, error: "Messages must be an array." };
  if (payload.messages.length < 1 || payload.messages.length > MAX_MESSAGES) return { ok: false, error: "Message count is outside the allowed range." };
  if (payload.max_tokens !== undefined && (!Number.isFinite(Number(payload.max_tokens)) || Number(payload.max_tokens) > MAX_TOKENS)) {
    return { ok: false, error: "max_tokens exceeds the allowed limit." };
  }

  for (const message of payload.messages) {
    if (!message || typeof message !== "object") return { ok: false, error: "Each message must be an object." };
    if (!["system", "user", "assistant"].includes(message.role)) return { ok: false, error: "Message role is not allowed." };
    if (typeof message.content !== "string") return { ok: false, error: "Message content must be text." };
    if (message.content.length > MAX_CONTENT_CHARS) return { ok: false, error: "Message content is too long." };
  }
  return { ok: true };
}

function checkRateLimit(request) {
  const key = request.headers.get("CF-Connecting-IP") || "unknown";
  const now = Date.now();
  const bucket = rateBuckets.get(key) || { count: 0, resetAt: now + RATE_LIMIT_WINDOW_MS };
  if (now > bucket.resetAt) {
    bucket.count = 0;
    bucket.resetAt = now + RATE_LIMIT_WINDOW_MS;
  }
  bucket.count += 1;
  rateBuckets.set(key, bucket);
  return { allowed: bucket.count <= RATE_LIMIT_MAX };
}

function safeUpstreamMessage(status) {
  if (status === 401 || status === 403) return "DeepSeek proxy credentials are not accepted.";
  if (status === 429) return "DeepSeek rate limit exceeded.";
  if (status === 400) return "DeepSeek rejected the request.";
  return "DeepSeek model unavailable.";
}

function jsonResponse(body, status = 200, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...headers,
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
