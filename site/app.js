(function () {
  const channelButtons = Array.from(document.querySelectorAll(".channel-button"));
  const messagesEl = document.querySelector("#messages");
  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");
  const pixGallery = document.querySelector("[data-pix-gallery]");
  const mainSlides = Array.from(document.querySelectorAll("[data-main-slide]"));
  const mainThumbs = Array.from(document.querySelectorAll("[data-main-thumb]"));
  const chatApiUrl = document.querySelector('meta[name="sow-chat-api"]')?.getAttribute("content")?.trim();
  let selectedChannel = "mind-philosophy";
  let selectedMainSlide = 0;

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

  addMsg("agent", "Pick a channel, then ask one short question.");

  loadPixGallery();
  setupMainCarousel();

  if (!chatApiUrl) {
    addMsg("agent", "Chat backend is not configured yet. Deploy worker/deepseek-proxy.js, then set the sow-chat-api meta tag in index.html to the Worker /chat URL.");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = promptEl.value.trim();
    if (!prompt) return;
      if (!chatApiUrl) {
      addMsg("agent", "Backend URL is missing. Configure the Cloudflare Worker /chat URL first.");
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
    const contextText = compactContextText(context, channel);
    const agentPrompt = formatAgentPrompt(agent, channelLabel);
    const systemPrompt = [
      "You are the Solar Oracle Walkman chatbot, but you must inhabit the selected agent profile instead of answering as a generic assistant.",
      "Use only the provided project context before answering. Do not claim you can browse GitHub or inspect repository files live.",
      "If asked what you can see, say you are reading the static public knowledge file that this page sends with each question.",
      "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
      "Keep every answer very short and easy to absorb: 1 to 3 short sentences, about 120 Chinese characters or fewer unless the user asks for detail. Avoid dense explanations. Invite the user to ask for more details if needed.",
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
          { role: "system", content: `Short project context from site/knowledge-base.json:\n${contextText}` },
          { role: "user", content: prompt }
        ],
        max_tokens: 140
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
      formatList("Default focus", limitList(agent.default_focus, 3)),
      formatList("Channel-specific themes", limitList(agent.medium_article_themes || agent.business_framing, 2)),
      formatList("Answer strategy", limitList(agent.answer_strategy, 2)),
      formatList("Avoid", agent.avoid)
    ];

    return parts.filter(Boolean).join(" ");
  }

  function compactContextText(context, channel) {
    const agent = context.agents?.[channel] || {};
    return [
      `Project: ${context.project}. Status: ${context.status}.`,
      `Summary: ${context.summary}`,
      `Agent thesis: ${agent.central_thesis || "Use the selected channel framing."}`,
      formatList("Agent focus", limitList(agent.default_focus, 3)),
      `Core workflow: ${limitList(context.core_workflow, 3).join(" -> ")}.`,
      `V1: ${context.v1_current_prototype?.main_value || "IV voiceprint smart contract prototype."}`,
      `Energy provenance boundary: ${context.energy_provenance_evidence?.meaning || "research evidence records, not legal certification."}`,
      formatList("Cannot claim", context.not_claimed_as),
      `Security boundary: ${context.security_boundary}`
    ].filter(Boolean).join("\n");
  }

  function limitList(values, maxItems) {
    return Array.isArray(values) ? values.slice(0, maxItems) : [];
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

  function setupMainCarousel() {
    if (mainSlides.length === 0) return;

    mainThumbs.forEach((thumb) => {
      thumb.addEventListener("click", () => showMainSlide(Number(thumb.dataset.mainThumb || 0)));
    });
    showMainSlide(0);
  }

  function showMainSlide(index) {
    selectedMainSlide = (index + mainSlides.length) % mainSlides.length;
    mainSlides.forEach((slide, slideIndex) => {
      const active = slideIndex === selectedMainSlide;
      slide.hidden = !active;
      slide.classList.toggle("active", active);
    });
    mainThumbs.forEach((thumb, thumbIndex) => {
      const active = thumbIndex === selectedMainSlide;
      thumb.classList.toggle("active", active);
      thumb.setAttribute("aria-selected", String(active));
    });

    if (window.instgrm?.Embeds) window.instgrm.Embeds.process();
    requestAnimationFrame(() => {
      document.querySelector(".slide-thumbs")?.scrollIntoView({ block: "nearest" });
    });
  }

  async function loadPixGallery() {
    if (!pixGallery) return;

    try {
      const response = await fetch("./pix/manifest.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`Pix manifest returned ${response.status}`);
      const items = await response.json();
      if (!Array.isArray(items) || items.length === 0) throw new Error("Pix manifest is empty.");

      pixGallery.replaceChildren(...items.map(createPixFigure));
    } catch (_error) {
      const fallback = document.createElement("p");
      fallback.className = "pix-empty";
      fallback.textContent = "PIX unavailable.";
      pixGallery.replaceChildren(fallback);
    }
  }

  function createPixFigure(item) {
    const src = typeof item === "string" ? item : item.src;
    const caption = typeof item === "string" ? titleFromFilename(item) : item.caption || titleFromFilename(src);
    const figure = document.createElement("figure");
    const image = document.createElement("img");
    const figcaption = document.createElement("figcaption");

    image.src = `./pix/${src}`;
    image.alt = caption;
    figcaption.textContent = caption;
    figure.append(image, figcaption);
    return figure;
  }

  function titleFromFilename(filename) {
    return String(filename || "PIX")
      .replace(/\.[^.]+$/, "")
      .replace(/[_-]+/g, " ");
  }
})();
