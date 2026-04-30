(function () {
  const ivGrid = document.querySelector("#iv-grid");
  if (ivGrid) setupIvDatabase(ivGrid);

  const pixGallery = document.querySelector("[data-pix-gallery]");
  const pixLightbox = pixGallery ? setupPixLightbox() : null;
  if (pixGallery) loadPixGallery(pixGallery, pixLightbox);

  const mainSlides = Array.from(document.querySelectorAll("[data-main-slide]"));
  const mainThumbs = Array.from(document.querySelectorAll("[data-main-thumb]"));
  if (mainSlides.length > 0) setupMainCarousel({ mainSlides, mainThumbs });

  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");
  const messagesEl = document.querySelector("#messages");
  if (form && promptEl && messagesEl) {
    setupIdentityMarquee({ form, promptEl });
    setupChat({ form, promptEl, messagesEl });
  }

  async function setupIvDatabase(grid) {
    try {
      const response = await fetch("./data/iv-records.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`IV records returned ${response.status}`);
      const records = await response.json();
      grid.replaceChildren(...records.map(createIvCard));
    } catch (_error) {
      const fallback = document.createElement("p");
      fallback.className = "iv-empty";
      fallback.textContent = "IV database unavailable.";
      grid.replaceChildren(fallback);
    }
  }

  function createIvCard(record) {
    const article = document.createElement("article");
    article.className = "iv-card";

    const frame = document.createElement("div");
    frame.className = "curve-frame";
    frame.append(createCurveSvg(record.points || []), createText("span", "curve-label", record.id || "iv-record"));

    const info = document.createElement("div");
    info.className = "iv-info";

    const buy = document.createElement("button");
    buy.className = "buy-button";
    buy.type = "button";
    buy.textContent = "Buy";

    info.append(
      buy,
      createText("h2", "song-title", record.title || "Untitled IV Curve"),
      createMeta("", record.light || "sunlight"),
      createMeta("7D fingerprint", formatFingerprint(record.fingerprint))
    );

    article.append(frame, info);
    return article;
  }

  function createCurveSvg(points) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "I-V curve point cloud");

    const sampled = sampleCurvePoints(points, 500);
    sampled.forEach(([x, y]) => {
      svg.append(svgEl("circle", { cx: x, cy: y, r: 0.32, class: "curve-point" }));
    });
    return svg;
  }

  function sampleCurvePoints(points, count) {
    if (!Array.isArray(points) || points.length === 0) return [];
    const normalized = points
      .map(([v, i]) => [Number(v), Number(i)])
      .filter(([v, i]) => Number.isFinite(v) && Number.isFinite(i))
      .sort((a, b) => a[0] - b[0]);
    if (normalized.length === 0) return [];
    const maxV = Math.max(...normalized.map(([v]) => v), 1);
    const maxI = Math.max(...normalized.map(([, i]) => i), 1);

    return Array.from({ length: count }, (_, index) => {
      const ratio = count === 1 ? 0 : index / (count - 1);
      const voltage = ratio * maxV;
      const current = interpolateCurrent(normalized, voltage);
      return [4 + (voltage / maxV) * 92, 96 - (current / maxI) * 92];
    });
  }

  function interpolateCurrent(points, voltage) {
    if (voltage <= points[0][0]) return points[0][1];
    for (let index = 1; index < points.length; index += 1) {
      const [rightV, rightI] = points[index];
      if (voltage <= rightV) {
        const [leftV, leftI] = points[index - 1];
        const segment = rightV - leftV || 1;
        const ratio = (voltage - leftV) / segment;
        return leftI + (rightI - leftI) * ratio;
      }
    }
    return points[points.length - 1][1];
  }

  function svgEl(name, attrs) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  }

  function createText(tag, className, text) {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    return element;
  }

  function createMeta(label, value) {
    const p = document.createElement("p");
    p.className = label === "Light source" ? "light-source" : "fingerprint";
    if (label) {
      const span = document.createElement("span");
      span.textContent = label;
      p.append(span);
    }
    p.append(document.createTextNode(value));
    return p;
  }

  function formatFingerprint(values) {
    return Array.isArray(values) ? values.map((value) => Number(value).toFixed(3)).join(" / ") : "n/a";
  }

  async function loadPixGallery(gallery, lightbox) {
    try {
      const response = await fetch("./pix/manifest.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`Pix manifest returned ${response.status}`);
      const items = await response.json();
      if (!Array.isArray(items) || items.length === 0) throw new Error("Pix manifest is empty.");
      gallery.replaceChildren(...items.map((item) => createPixFigure(item, lightbox)));
    } catch (_error) {
      gallery.replaceChildren(createText("p", "pix-empty", "PIX unavailable."));
    }
  }

  function createPixFigure(item, lightbox) {
    const src = typeof item === "string" ? item : item.src;
    const caption = typeof item === "string" ? titleFromFilename(item) : item.caption || titleFromFilename(src);
    const figure = document.createElement("figure");
    const button = document.createElement("button");
    const image = document.createElement("img");
    const figcaption = document.createElement("figcaption");
    const fullSrc = `./pix/${src}`;
    button.className = "pix-open";
    button.type = "button";
    button.setAttribute("aria-label", `Open large image: ${caption}`);
    button.addEventListener("click", () => lightbox?.open(fullSrc, caption));
    image.src = fullSrc;
    image.alt = caption;
    figcaption.textContent = caption;
    button.append(image);
    figure.append(button, figcaption);
    return figure;
  }

  function setupPixLightbox() {
    const overlay = document.createElement("div");
    const closeButton = document.createElement("button");
    const image = document.createElement("img");
    const caption = document.createElement("p");

    overlay.className = "pix-lightbox";
    overlay.hidden = true;
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Large project photo");

    closeButton.className = "pix-lightbox-close";
    closeButton.type = "button";
    closeButton.setAttribute("aria-label", "Close large image");
    closeButton.textContent = "Close";

    caption.className = "pix-lightbox-caption";
    overlay.append(closeButton, image, caption);
    document.body.append(overlay);

    closeButton.addEventListener("click", close);
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) close();
    });
    document.addEventListener("keydown", (event) => {
      if (!overlay.hidden && event.key === "Escape") close();
    });

    function open(src, text) {
      image.src = src;
      image.alt = text;
      caption.textContent = text;
      overlay.hidden = false;
      document.body.classList.add("lightbox-open");
      closeButton.focus();
    }

    function close() {
      overlay.hidden = true;
      document.body.classList.remove("lightbox-open");
    }

    return { open };
  }

  function titleFromFilename(filename) {
    return String(filename || "PIX")
      .replace(/\.[^.]+$/, "")
      .replace(/[_-]+/g, " ");
  }

  function setupMainCarousel({ mainSlides, mainThumbs }) {
    let selectedMainSlide = 0;
    mainThumbs.forEach((thumb) => {
      thumb.addEventListener("click", () => showMainSlide(Number(thumb.dataset.mainThumb || 0)));
    });
    showMainSlide(0);

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
    }
  }

  function setupChat({ form, promptEl, messagesEl }) {
    const channelButtons = Array.from(document.querySelectorAll(".channel-button"));
    const chatApiUrl = document.querySelector('meta[name="sow-chat-api"]')?.getAttribute("content")?.trim();
    let selectedChannel = "mind-philosophy";
    const visibleScrollbar = setupVisibleScrollbar(messagesEl);

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
        const responseText = await askBackendChat({ prompt, channel: selectedChannel, context, chatApiUrl });
        updateMsg(thinkingMsg, "agent", responseText);
      } catch (error) {
        updateMsg(thinkingMsg, "agent", `Error: ${error.message}`);
      }
    });

    function addMsg(role, text) {
      const div = document.createElement("div");
      div.className = `msg ${role === "user" ? "user" : "agent"}`;
      div.textContent = `${role === "user" ? "You" : "Agent"}: ${text}`;
      messagesEl.appendChild(div);
      scrollToBottom();
      return div;
    }

    function updateMsg(element, role, text) {
      element.className = `msg ${role === "user" ? "user" : "agent"}`;
      element.textContent = `${role === "user" ? "You" : "Agent"}: ${text}`;
      scrollToBottom();
    }

    function scrollToBottom() {
      requestAnimationFrame(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
        visibleScrollbar.update();
      });
    }
  }

  function setupVisibleScrollbar(messagesEl) {
    const track = messagesEl.parentElement?.querySelector(".messages-scrollbar");
    const thumb = track?.querySelector(".messages-scrollbar-thumb");
    if (!track || !thumb) return { update() {} };

    let dragging = false;
    let dragStartY = 0;
    let startScrollTop = 0;

    messagesEl.addEventListener("scroll", update);
    track.addEventListener("wheel", (event) => {
      event.preventDefault();
      messagesEl.scrollTop += event.deltaY;
    }, { passive: false });
    window.addEventListener("resize", update);
    new ResizeObserver(update).observe(messagesEl);
    new MutationObserver(update).observe(messagesEl, { childList: true, subtree: true, characterData: true });

    track.addEventListener("pointerdown", (event) => {
      const rect = track.getBoundingClientRect();
      const thumbRect = thumb.getBoundingClientRect();
      if (event.clientY < thumbRect.top || event.clientY > thumbRect.bottom) {
        const ratio = (event.clientY - rect.top) / Math.max(rect.height, 1);
        messagesEl.scrollTop = ratio * messagesEl.scrollHeight - messagesEl.clientHeight / 2;
      }
      dragging = true;
      dragStartY = event.clientY;
      startScrollTop = messagesEl.scrollTop;
      thumb.classList.add("dragging");
      track.setPointerCapture(event.pointerId);
      update();
    });

    track.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      const maxScroll = messagesEl.scrollHeight - messagesEl.clientHeight;
      const maxThumbTop = track.clientHeight - thumb.offsetHeight;
      messagesEl.scrollTop = startScrollTop + ((event.clientY - dragStartY) / Math.max(maxThumbTop, 1)) * maxScroll;
    });

    track.addEventListener("pointerup", stopDragging);
    track.addEventListener("pointercancel", stopDragging);

    update();

    function stopDragging(event) {
      dragging = false;
      thumb.classList.remove("dragging");
      if (track.hasPointerCapture(event.pointerId)) track.releasePointerCapture(event.pointerId);
    }

    function update() {
      const visibleRatio = messagesEl.clientHeight / Math.max(messagesEl.scrollHeight, 1);
      const thumbHeight = Math.max(track.clientHeight * visibleRatio, 34);
      const maxScroll = messagesEl.scrollHeight - messagesEl.clientHeight;
      const maxThumbTop = track.clientHeight - thumbHeight;
      const top = maxScroll > 0 ? (messagesEl.scrollTop / maxScroll) * maxThumbTop : 0;

      thumb.style.height = `${Math.min(thumbHeight, track.clientHeight)}px`;
      thumb.style.transform = `translateY(${Math.max(0, top)}px)`;
      thumb.hidden = maxScroll <= 1;
      track.classList.toggle("disabled", maxScroll <= 1);
    }

    return { update };
  }

  function setupIdentityMarquee({ form, promptEl }) {
    document.querySelectorAll(".identity-marquee button").forEach((button) => {
      button.addEventListener("click", () => {
        promptEl.value = button.textContent.trim();
        form.requestSubmit();
      });
    });
  }

  async function loadLocalContext() {
    const response = await fetch("./knowledge-base.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Knowledge base returned ${response.status}`);
    return await response.json();
  }

  async function askBackendChat({ prompt, channel, context, chatApiUrl }) {
    const channelLabel = channel === "innovative-startup" ? "innovative startup 研發新創" : "mind philosophy 心智哲學";
    const agent = context.agents?.[channel] || {};
    const contextText = compactContextText(context, channel);
    const agentPrompt = formatAgentPrompt(agent, channelLabel);
    const systemPrompt = [
      "You are the Solar Oracle Walkman chatbot, but you must inhabit the selected agent profile instead of answering as a generic assistant.",
      "Use only the provided project context before answering. Do not claim you can browse GitHub or inspect repository files live.",
      "If asked what you can see, say you are reading the static public knowledge file that this page sends with each question.",
      "Use precise boundary language: public research prototype; not legal REC; not T-REC; not energy equivalence; not financial product.",
      "If asked about SBIR, answer from the provided public_funding_status. Do not say the project has not applied for or has not passed SBIR.",
      "Keep answers concise but not too short: usually 2 to 5 short sentences, about 240 Chinese characters or fewer unless the user asks for detail. Avoid dense explanations. Invite the user to ask for more details if needed.",
      "If asked about music or sound, do not say it is not a music work. Explain that it began as a sound sculpture and generative music prototype, while the current public site also frames it as identity and evidence research.",
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
        max_tokens: 280
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
      context.public_funding_status ? `Public funding/R&D status: ${context.public_funding_status}` : "",
      `Summary: ${context.summary}`,
      context.sound_origin ? `Sound/music origin: ${context.sound_origin}` : "",
      context.collaborators ? formatList("Collaborators", Object.values(context.collaborators)) : "",
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

  function cleanResponse(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/__(.*?)__/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .trim();
  }
})();
