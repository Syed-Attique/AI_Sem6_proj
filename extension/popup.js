const statusBadge = document.getElementById("statusBadge");
const currentUrl = document.getElementById("currentUrl");
const riskScore = document.getElementById("riskScore");
const message = document.getElementById("message");
const scanButton = document.getElementById("scanButton");
const markLegitButton = document.getElementById("markLegitButton");
let lastResult = null;

function setStatus(label, className) {
  statusBadge.textContent = label;
  statusBadge.className = `badge ${className}`;
}

function setRiskState(className) {
  riskScore.className = `score ${className}`;
  riskScore.parentElement.className = `risk-panel ${className}`;
}

function renderResult(result) {
  lastResult = result;
  currentUrl.textContent = result.url || "-";
  markLegitButton.hidden = result.prediction !== "phishing";

  if (result.prediction === "phishing") {
    setStatus("Suspicious", "danger");
    setRiskState("danger");
    riskScore.textContent = `${Math.round(result.risk_score * 100)}%`;
    message.textContent = "Avoid entering passwords, card details, or personal information.";
  } else if (result.prediction === "legitimate") {
    setStatus("Safe", "safe");
    setRiskState("safe");
    riskScore.textContent = `${Math.round(result.risk_score * 100)}%`;
    message.textContent = "No phishing pattern was detected for this URL.";
  } else {
    setStatus("Unavailable", "neutral");
    setRiskState("neutral");
    riskScore.textContent = "-";
    message.textContent = result.error || "Scanner unavailable.";
  }
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

async function loadStoredResult(tabId, url) {
  currentUrl.textContent = url || "-";
  const stored = await chrome.storage.local.get(`scan:${tabId}`);
  const result = stored[`scan:${tabId}`];

  if (result && result.url === url) {
    renderResult(result);
  } else {
    await scanCurrentTab();
  }
}

async function scanCurrentTab() {
  const tab = await getActiveTab();
  if (!tab?.url) {
    renderResult({ prediction: "unavailable", error: "No active tab URL found." });
    return;
  }

  scanButton.disabled = true;
  setStatus("Scanning", "neutral");
  setRiskState("neutral");
  currentUrl.textContent = tab.url;

  chrome.runtime.sendMessage({ type: "SCAN_URL", tabId: tab.id, url: tab.url }, async (response) => {
    scanButton.disabled = false;

    if (chrome.runtime.lastError) {
      renderResult({
        url: tab.url,
        prediction: "unavailable",
        error: chrome.runtime.lastError.message,
      });
      return;
    }

    if (response?.ok) {
      await chrome.storage.local.set({ [`scan:${tab.id}`]: response.result });
      renderResult(response.result);
    } else {
      renderResult({
        url: tab.url,
        prediction: "unavailable",
        error: response?.error || "Scanner unavailable.",
      });
    }
  });
}

async function markCurrentTabLegitimate() {
  const tab = await getActiveTab();
  const url = lastResult?.url || tab?.url;

  if (!tab?.id || !url) {
    renderResult({ prediction: "unavailable", error: "No active tab URL found." });
    return;
  }

  markLegitButton.disabled = true;
  markLegitButton.textContent = "Saving...";

  chrome.runtime.sendMessage(
    { type: "MARK_LEGITIMATE", tabId: tab.id, url },
    async (response) => {
      markLegitButton.disabled = false;
      markLegitButton.textContent = "Mark as Legit";

      if (chrome.runtime.lastError || !response?.ok) {
        message.textContent = chrome.runtime.lastError?.message || response?.error || "Could not save feedback.";
        return;
      }

      await chrome.storage.local.set({ [`scan:${tab.id}`]: response.scanResult });
      renderResult(response.scanResult);
      message.textContent = "Saved as legitimate. Future scans will trust this site.";
    }
  );
}

scanButton.addEventListener("click", scanCurrentTab);
markLegitButton.addEventListener("click", markCurrentTabLegitimate);

getActiveTab().then((tab) => {
  loadStoredResult(tab?.id, tab?.url);
});
