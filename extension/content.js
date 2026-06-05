function showWarning(result) {
  if (document.getElementById("ai-phishing-detector-overlay")) {
    return;
  }

  const riskPercent = Math.round(result.risk_score * 100);
  const overlay = document.createElement("div");
  overlay.id = "ai-phishing-detector-overlay";
  overlay.innerHTML = `
    <div class="ai-pd-shell" role="dialog" aria-modal="true" aria-labelledby="ai-pd-title">
      <div class="ai-pd-topline">
        <div class="ai-pd-icon" aria-hidden="true">
          <svg width="23" height="23" viewBox="0 0 24 24" fill="none">
            <circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="2"></circle>
            <path d="M15.5 15.5L21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
          </svg>
        </div>
        <span>Threat check</span>
      </div>
      <h1 id="ai-pd-title">This page may be phishing</h1>
      <p class="ai-pd-copy">Risk score <strong>${riskPercent}%</strong>. Avoid entering passwords, card details, seed phrases, or personal information here.</p>
      <p class="ai-pd-url">${result.url || window.location.href}</p>
      <div class="ai-pd-actions">
        <button type="button" class="ai-pd-primary" id="ai-pd-go-back">Go Back</button>
        <button type="button" class="ai-pd-trust" id="ai-pd-mark-legit">Mark as Legit</button>
        <button type="button" class="ai-pd-secondary" id="ai-pd-continue">Continue Anyway</button>
      </div>
    </div>
  `;

  const style = document.createElement("style");
  style.textContent = `
    #ai-phishing-detector-overlay {
      position: fixed;
      inset: 0;
      z-index: 2147483647;
      display: grid;
      place-items: center;
      min-height: 100vh;
      padding: 24px;
      color: #f9fafb;
      background:
        radial-gradient(circle at 50% 0%, rgba(239, 68, 68, 0.20), transparent 34%),
        radial-gradient(circle at 0% 100%, rgba(245, 158, 11, 0.12), transparent 28%),
        rgba(2, 6, 10, 0.94);
      font-family: Arial, sans-serif;
      backdrop-filter: blur(10px);
    }

    #ai-phishing-detector-overlay * {
      box-sizing: border-box;
    }

    .ai-pd-shell {
      position: relative;
      width: min(500px, 100%);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 22px;
      padding: 28px;
      text-align: left;
      background: linear-gradient(180deg, rgba(18, 24, 32, 0.78), rgba(5, 8, 13, 0.76));
      box-shadow: 0 28px 90px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.10);
      backdrop-filter: blur(22px);
    }

    .ai-pd-topline {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      border: 1px solid rgba(248, 113, 113, 0.32);
      border-radius: 999px;
      padding: 7px 11px 7px 8px;
      color: #fecaca;
      background: rgba(127, 29, 29, 0.28);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .ai-pd-icon {
      width: 26px;
      height: 26px;
      display: grid;
      place-items: center;
      border-radius: 999px;
      color: #450a0a;
      background: #fca5a5;
    }

    .ai-pd-shell h1 {
      margin: 22px 0 10px;
      color: #f8fafc;
      font-size: 30px;
      font-weight: 700;
      letter-spacing: 0;
    }

    .ai-pd-copy {
      margin: 0 0 18px;
      color: #cbd5e1;
      font-size: 15px;
      line-height: 1.55;
    }

    .ai-pd-url {
      max-height: 72px;
      margin: 0 0 24px;
      overflow: auto;
      overflow-wrap: anywhere;
      border: 1px solid rgba(255, 255, 255, 0.10);
      border-radius: 14px;
      padding: 12px;
      color: #94a3b8;
      background: rgba(2, 6, 23, 0.38);
      font-size: 12px;
      line-height: 1.4;
    }

    .ai-pd-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .ai-pd-actions button {
      flex: 1 1 180px;
      border-radius: 999px;
      padding: 12px 16px;
      font: 700 14px Arial, sans-serif;
      cursor: pointer;
    }

    .ai-pd-primary {
      border: 1px solid rgba(248, 113, 113, 0.40);
      color: #ffffff;
      background: linear-gradient(180deg, #dc2626, #991b1b);
    }

    .ai-pd-secondary {
      border: 1px solid rgba(255, 255, 255, 0.14);
      color: #e5e7eb;
      background: rgba(255, 255, 255, 0.06);
    }

    .ai-pd-trust {
      border: 1px solid rgba(74, 222, 128, 0.38);
      color: #ffffff;
      background: linear-gradient(180deg, #16a34a, #166534);
    }
  `;

  document.documentElement.appendChild(style);
  document.documentElement.appendChild(overlay);

  document.getElementById("ai-pd-go-back").addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "GO_BACK" });
  });

  document.getElementById("ai-pd-continue").addEventListener("click", () => {
    overlay.remove();
    style.remove();
  });

  document.getElementById("ai-pd-mark-legit").addEventListener("click", () => {
    const button = document.getElementById("ai-pd-mark-legit");
    button.textContent = "Saving...";
    button.disabled = true;

    chrome.runtime.sendMessage(
      { type: "MARK_LEGITIMATE", url: result.url || window.location.href },
      (response) => {
        if (chrome.runtime.lastError || !response?.ok) {
          button.textContent = "Could not save";
          button.disabled = false;
          return;
        }

        overlay.remove();
        style.remove();
      }
    );
  });
}

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "PHISHING_WARNING") {
    showWarning(message.result);
  } else if (message.type === "MARKED_LEGITIMATE") {
    const overlay = document.getElementById("ai-phishing-detector-overlay");
    overlay?.remove();
  }
});

chrome.runtime.sendMessage({ type: "GET_CURRENT_SCAN" }, (response) => {
  if (chrome.runtime.lastError || !response?.ok || !response.result) {
    return;
  }

  if (
    response.result.prediction === "phishing" &&
    response.result.url === window.location.href
  ) {
    showWarning(response.result);
  }
});
