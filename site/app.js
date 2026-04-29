(function () {
  const audienceSelect = document.querySelector("#audience");
  const messagesEl = document.querySelector("#messages");
  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");
  const chatApiUrl = document
    .querySelector('meta[name="sow-chat-api"]')
    ?.getAttribute("content") || "/api/chat";

  promptEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  addMsg("agent", "Ready. I can explain plans for investors or art audiences based on local project materials.");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = promptEl.value.trim();
    if (!prompt) return;
    addMsg("user", prompt);
    promptEl.value = "";

    try {
      const context = await loadLocalContext();
      const responseText = await askBackendChat({ prompt, audience: audienceSelect.value, context });
      addMsg("agent", responseText);
    } catch (error) {
      addMsg("agent", `Error: ${error.message}`);
    }
  });

  async function loadLocalContext() {
    const files = ["../README.md", "./knowledge-base.json", "../docs/10_public_disclaimer.md", "../docs/00_project_overview.md"];
    const entries = await Promise.all(
      files.map(async (url) => {
        try {
          const res = await fetch(url);
          if (!res.ok) return `${url}: unavailable`;
          return `${url}:\n${await res.text()}`;
        } catch {
          return `${url}: unavailable`;
        }
      })
    );
    return entries.join("\n\n---\n\n");
  }

  async function askBackendChat({ prompt, audience, context }) {
    const systemPrompt = [
      "You are the Solar Oracle Walkman agent.",
      "Use the provided repository context before answering.",
      "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
      `Primary audience: ${audience}.`,
      "Task: explain and structure plans clearly for either investors or art audience members."
    ].join(" ");

    const res = await fetch(chatApiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        audience,
        systemPrompt,
        context,
        prompt
      })
    });

    if (!res.ok) {
      const errText = await res.text();
      if (res.status === 405 || res.status === 404) {
        return askOpenAIFromLocalKey({ systemPrompt, prompt, audience, context });
      }
      throw new Error(`Backend chat API ${res.status}: ${errText}`);
    }

    const data = await res.json();
    return data.choices?.[0]?.message?.content?.trim() || "No response content.";
  }

  function readLocalApiKey() {
    const candidates = [
      "OPENAI_API_KEY",
      "openai_api_key",
      "openai-key",
      "sow_openai_api_key"
    ];
    for (const keyName of candidates) {
      const val = window.localStorage.getItem(keyName);
      if (val && val.startsWith("sk-")) return val.trim();
    }
    return null;
  }

  async function askOpenAIFromLocalKey({ systemPrompt, prompt, audience, context }) {
    const apiKey = readLocalApiKey();
    if (!apiKey) {
      throw new Error(
        "Backend unavailable and no local API key found. Save OPENAI_API_KEY in localStorage for this browser."
      );
    }

    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: "gpt-4.1-mini",
        temperature: 0.2,
        messages: [
          { role: "system", content: systemPrompt },
          {
            role: "system",
            content: `Audience: ${audience}\n\nProject context:\n${context}`
          },
          { role: "user", content: prompt }
        ]
      })
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Local OpenAI API ${res.status}: ${errText}`);
    }

    const data = await res.json();
    return data.choices?.[0]?.message?.content?.trim() || "No response content.";
  }

  function addMsg(role, text) {
    const div = document.createElement("div");
    div.className = `msg ${role === "user" ? "user" : "agent"}`;
    div.textContent = `${role === "user" ? "You" : "Agent"}: ${text}`;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
})();
