const API_URL = "http://127.0.0.1:5000/predict";
const MARK_LEGITIMATE_URL = "http://127.0.0.1:5000/mark-legitimate";

async function scanUrl(url) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Scanner unavailable");
  }
  return data;
}

async function markLegitimate(url) {
  const response = await fetch(MARK_LEGITIMATE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Could not mark website as legitimate");
  }
  return data;
}

function notifyPhishing(tabId, result, attempt = 0) {
  chrome.tabs.sendMessage(tabId, {
    type: "PHISHING_WARNING",
    result,
  }).catch(() => {
    if (attempt < 4) {
      setTimeout(() => notifyPhishing(tabId, result, attempt + 1), 300);
    }
  });
}

async function scanAndStore(tabId, url) {
  if (
    !url ||
    url.startsWith("chrome://") ||
    url.startsWith("edge://") ||
    url.startsWith("about:") ||
    url.startsWith("file://")
  ) {
    return;
  }

  try {
    const result = await scanUrl(url);
    await chrome.storage.local.set({ [`scan:${tabId}`]: result });

    if (result.prediction === "phishing") {
      chrome.notifications.create(`phishing-${tabId}-${Date.now()}`, {
        type: "basic",
        iconUrl: "icon-128.png",
        title: "Suspicious Website Detected",
        message: "Avoid entering passwords, payment details, or personal information on this page.",
        priority: 2,
      });

      notifyPhishing(tabId, result);
    }
  } catch (error) {
    await chrome.storage.local.set({
      [`scan:${tabId}`]: {
        url,
        prediction: "unavailable",
        risk_score: null,
        error: error.message,
      },
    });
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if ((changeInfo.status === "complete" || changeInfo.url) && tab.url) {
    scanAndStore(tabId, tab.url);
  }
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const tab = await chrome.tabs.get(tabId);
  if (tab?.url) {
    scanAndStore(tabId, tab.url);
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GO_BACK") {
    const tabId = sender.tab?.id || message.tabId;
    if (!tabId) {
      sendResponse({ ok: false, error: "No tab found" });
      return true;
    }

    chrome.tabs.goBack(tabId, () => {
      if (chrome.runtime.lastError) {
        chrome.tabs.update(tabId, { url: "chrome://newtab/" });
      }
      sendResponse({ ok: true });
    });

    return true;
  }

  if (message.type === "MARK_LEGITIMATE") {
    markLegitimate(message.url)
      .then(async (result) => {
        const tabId = message.tabId || sender.tab?.id;
        const scanResult = {
          url: message.url,
          prediction: "legitimate",
          risk_score: 0.01,
          source: "user_feedback",
        };

        if (tabId) {
          await chrome.storage.local.set({ [`scan:${tabId}`]: scanResult });
          chrome.tabs.sendMessage(tabId, {
            type: "MARKED_LEGITIMATE",
            result: scanResult,
          }).catch(() => {});
        }

        sendResponse({ ok: true, result, scanResult });
      })
      .catch((error) => {
        sendResponse({ ok: false, error: error.message });
      });

    return true;
  }

  if (message.type === "GET_CURRENT_SCAN") {
    const tabId = sender.tab?.id || message.tabId;
    if (!tabId) {
      sendResponse({ ok: false, error: "No tab found" });
      return true;
    }

    chrome.storage.local.get(`scan:${tabId}`).then((stored) => {
      sendResponse({ ok: true, result: stored[`scan:${tabId}`] || null });
    });

    return true;
  }

  if (message.type !== "SCAN_URL") {
    return false;
  }

  scanUrl(message.url)
    .then((result) => {
      const tabId = message.tabId || sender.tab?.id;
      if (tabId) {
        chrome.storage.local.set({ [`scan:${tabId}`]: result });
        if (result.prediction === "phishing") {
          notifyPhishing(tabId, result);
        }
      }
      sendResponse({ ok: true, result });
    })
    .catch((error) => {
      sendResponse({ ok: false, error: error.message });
    });

  return true;
});
