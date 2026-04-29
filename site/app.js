(function () {
  const audienceSelect = document.querySelector("#audience");
  const messagesEl = document.querySelector("#messages");
  const form = document.querySelector("#chat-form");
  const promptEl = document.querySelector("#prompt");

  addMsg("agent", "Ready. Server-side key mode is active.");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const prompt = promptEl.value.trim();
    if (!prompt) return;

    addMsg("user", prompt);
    promptEl.value = "";

    try {
      const context = await loadLocalContext();
      const responseText = await askServerAgent({ prompt, audience: audienceSelect.value, context });
      addMsg("agent", responseText);
    } catch (error) {
      addMsg("agent", `Error: ${error.message}`);
    }
  });

  async function loadLocalContext() {
    const files = ["../README.md", "./knowledge-base.json", "../docs/10_public_disclaimer.md", "../docs/00_project_overview.md"];
    const entries = await Promise.all(files.map(fetchTextOrUnavailable));
    return entries.join("\n\n---\n\n");
  }

  async function fetchTextOrUnavailable(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) return `${url}: unavailable`;
      return `${url}:\n${await res.text()}`;
    } catch {
      return `${url}: unavailable`;
    }
  }

  async function askServerAgent({ prompt, audience, context }) {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, audience, context })
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Server API ${res.status}: ${errText}`);
    }

    const data = await res.json();
    return data.answer || "No response content.";
  }

  function addMsg(role, text) {
    const div = document.createElement("div");
    div.className = `msg ${role === "user" ? "user" : "agent"}`;
    div.textContent = `${role === "user" ? "You" : "Agent"}: ${text}`;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
})();
