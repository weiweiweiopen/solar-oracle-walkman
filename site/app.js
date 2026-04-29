(function () {
  const keyInput = document.querySelector("#api-key");
  const audienceSelect = document.querySelector("#audience");
  const messagesEl = document.querySelector("#messages");
  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");

  keyInput.value = localStorage.getItem("deepseek_api_key") || "";
  keyInput.addEventListener("change", () => {
    localStorage.setItem("deepseek_api_key", keyInput.value.trim());
  });

  addMsg("agent", "Ready. I can explain plans for investors or art audiences based on local project materials.");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = promptEl.value.trim();
    if (!prompt) return;
    const apiKey = keyInput.value.trim();
    if (!apiKey) {
      addMsg("agent", "Please enter your DeepSeek API key first.");
      return;
    }

    addMsg("user", prompt);
    promptEl.value = "";

    try {
      const context = await loadLocalContext();
      const responseText = await askDeepSeek({ apiKey, prompt, audience: audienceSelect.value, context });
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

  async function askDeepSeek({ apiKey, prompt, audience, context }) {
    const systemPrompt = [
      "You are the Solar Oracle Walkman agent.",
      "Use the provided repository context before answering.",
      "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
      `Primary audience: ${audience}.`,
      "Task: explain and structure plans clearly for either investors or art audience members."
    ].join(" ");

    const res = await fetch("https://api.deepseek.com/chat/completions", {
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

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`DeepSeek API ${res.status}: ${errText}`);
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
