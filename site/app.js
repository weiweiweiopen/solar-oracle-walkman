(function () {
  const channelButtons = Array.from(document.querySelectorAll(".channel-button"));
  const messagesEl = document.querySelector("#messages");
  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");
  const chatApiUrl = document.querySelector('meta[name="sow-chat-api"]')?.getAttribute("content")?.trim();
  let selectedChannel = "mind-philosophy";

  channelButtons.forEach((button) => {
    button.addEventListener("click", () => {
      selectedChannel = button.dataset.channel;
      channelButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("active", active);
        item.setAttribute("aria-pressed", String(active));
      });
    });
  });

  promptEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  addMsg("agent", "Ready. Choose a channel, then ask me about Solar Oracle Walkman.");

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
      const responseText = await askBackendChat({ prompt, channel: selectedChannel, context });
      updateMsg(thinkingMsg, "agent", responseText);
    } catch (error) {
      updateMsg(thinkingMsg, "agent", `Error: ${error.message}`);
    }
  });

  async function loadLocalContext() {
    const response = await fetch("./knowledge-base.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Knowledge base returned ${response.status}`);
    return await response.json();
  }

  async function askBackendChat({ prompt, channel, context }) {
    const channelLabel = channel === "innovative-startup" ? "innovative startup 研發新創" : "mind philosophy 心智哲學";
    const agent = context.agents?.[channel] || {};
    const contextText = JSON.stringify(context, null, 2);
    const agentPrompt = formatAgentPrompt(agent, channelLabel);
    const systemPrompt = [
      "You are the Solar Oracle Walkman chatbot, but you must inhabit the selected agent profile instead of answering as a generic assistant.",
      "Use only the provided project context before answering. Do not claim you can browse GitHub or inspect repository files live.",
      "If asked what you can see, say you are reading the static public knowledge file that this page sends with each question.",
      "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
      `Response channel: ${channelLabel}.`,
      agentPrompt,
      "Do not blend the two channel personalities. If the user selected mind philosophy, prioritize identity, perception, material witness, energy layer, and mind-philosophy framing. If the user selected innovative startup, prioritize roadmap, stakeholders, protocol design, technical status, business layout, and risk boundaries.",
      "Answer in natural conversational language. Do not use Markdown formatting, asterisks, bold syntax, headings, numbered lists, or bullet lists unless the user explicitly asks for a list.",
      "Use Traditional Chinese when the user writes Chinese; otherwise use clear English.",
      "Task: explain the project clearly in the selected channel without overclaiming."
    ].join(" ");

    const response = await fetch(chatApiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "chat",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "system", content: `Channel: ${channelLabel}\n\nProject context file: site/knowledge-base.json\n\nProject context:\n${contextText}` },
          { role: "user", content: prompt }
        ],
        max_tokens: 650
      })
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Chat API returned ${response.status}`);
    return cleanResponse(data.content?.trim() || "No response content.");
  }

  function formatAgentPrompt(agent, channelLabel) {
    const parts = [
      `Selected agent: ${agent.name || channelLabel}.`,
      agent.audience ? `Audience: ${agent.audience}.` : "",
      agent.voice ? `Voice: ${agent.voice}.` : "",
      agent.central_thesis ? `Central thesis: ${agent.central_thesis}` : "",
      formatList("Default focus", agent.default_focus),
      formatList("Channel-specific themes", agent.medium_article_themes || agent.business_framing),
      formatList("Answer strategy", agent.answer_strategy),
      formatList("Avoid", agent.avoid)
    ];

    return parts.filter(Boolean).join(" ");
  }

  function formatList(label, values) {
    if (!Array.isArray(values) || values.length === 0) return "";
    return `${label}: ${values.join("; ")}.`;
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

  function cleanResponse(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/__(.*?)__/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .trim();
  }
})();
