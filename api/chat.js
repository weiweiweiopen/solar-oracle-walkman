export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const apiKey = process.env.DEEPSEEK_API_KEY;
  if (!apiKey) {
    res.status(500).json({ error: "Server missing DEEPSEEK_API_KEY" });
    return;
  }

  const { prompt = "", audience = "investor", context = "" } = req.body || {};
  if (!prompt.trim()) {
    res.status(400).json({ error: "Prompt is required" });
    return;
  }

  const systemPrompt = [
    "You are the Solar Oracle Walkman agent.",
    "Use the provided repository context before answering.",
    "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
    `Primary audience: ${audience}.`,
    "Task: explain and structure plans clearly for either investors or art audience members."
  ].join(" ");

  const upstream = await fetch("https://api.deepseek.com/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: "deepseek-chat",
      temperature: 0.3,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `Repository context:\n${context}\n\nUser request:\n${prompt}` }
      ]
    })
  });

  const text = await upstream.text();
  if (!upstream.ok) {
    res.status(upstream.status).send(text);
    return;
  }

  const data = JSON.parse(text);
  res.status(200).json({ answer: data.choices?.[0]?.message?.content?.trim() || "No response content." });
}
