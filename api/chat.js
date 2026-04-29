const DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions";

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  const apiKey = process.env.DEEPSEEK_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: "Missing DEEPSEEK_API_KEY" });
  }

  const { systemPrompt = "", prompt = "", audience = "general", context = "" } = req.body || {};
  if (!prompt || typeof prompt !== "string") {
    return res.status(400).json({ error: "prompt is required" });
  }

  try {
    const upstream = await fetch(DEEPSEEK_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        temperature: 0.2,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "system", content: `Audience: ${audience}\n\nProject context:\n${context}` },
          { role: "user", content: prompt }
        ]
      })
    });

    const payload = await upstream.json();
    return res.status(upstream.status).json(payload);
  } catch (error) {
    return res.status(502).json({ error: `Upstream error: ${error.message}` });
  }
};
