(function () {
  const audienceSelect = document.querySelector("#audience");
  const messagesEl = document.querySelector("#messages");
  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");
  const chatApiUrl = document.querySelector('meta[name="sow-chat-api"]')?.getAttribute("content")?.trim();

  promptEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  addMsg("agent", "Ready. I can explain Solar Oracle Walkman for investors or art audiences based on the project knowledge base.");

  if (!chatApiUrl) {
    addMsg("agent", "Chat backend is not configured yet. Deploy worker/deepseek-proxy.js, then set the sow-chat-api meta tag in index.html to the Worker /chat URL.");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = promptEl.value.trim();
    if (!prompt) return;
    if (!chatApiUrl) {
      addMsg("agent", "Backend URL is missing. GitHub Pages cannot store API keys; the Cloudflare Worker URL must be configured first.");
      return;
    }

    addMsg("user", prompt);
    promptEl.value = "";
    const thinkingMsg = addMsg("agent", "Thinking...");

    try {
      const context = await loadLocalContext();
      const responseText = await askBackendChat({ prompt, audience: audienceSelect.value, context });
      updateMsg(thinkingMsg, "agent", responseText);
    } catch (error) {
      updateMsg(thinkingMsg, "agent", `Error: ${error.message}`);
    }
  });

  async function loadLocalContext() {
    const response = await fetch("./knowledge-base.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Knowledge base returned ${response.status}`);
    return JSON.stringify(await response.json(), null, 2);
  }

  async function askBackendChat({ prompt, audience, context }) {
    const systemPrompt = [
      "You are the Solar Oracle Walkman agent.",
      "Use the provided project context before answering.",
      "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
      `Primary audience: ${audience}.`,
      "Task: explain and structure plans clearly for either investors or art audience members."
    ].join(" ");

    const response = await fetch(chatApiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "chat",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "system", content: `Audience: ${audience}\n\nProject context:\n${context}` },
          { role: "user", content: prompt }
        ],
        max_tokens: 550
      })
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Chat API returned ${response.status}`);
    return data.content?.trim() || "No response content.";
  }

  function addMsg(role, text) {
    const div = document.createElement("div");
    div.className = `msg ${role === "user" ? "user" : "agent"}`;
    div.textContent = `${role === "user" ? "You" : "Agent"}: ${text}`;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function updateMsg(element, role, text) {
    element.className = `msg ${role === "user" ? "user" : "agent"}`;
    element.textContent = `${role === "user" ? "You" : "Agent"}: ${text}`;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
})();
