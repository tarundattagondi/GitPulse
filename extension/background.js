// Service worker: handles cross-tab messaging and extension lifecycle events.

// Forward messages between popup and content scripts if needed
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getTabInfo') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        sendResponse({ tabId: tabs[0].id, url: tabs[0].url });
      } else {
        sendResponse({ error: 'No active tab' });
      }
    });
    return true; // async response
  }

  if (message.action === 'extractJDFromTab') {
    const tabId = message.tabId;
    chrome.tabs.sendMessage(tabId, { action: 'extractJD' }, (response) => {
      if (chrome.runtime.lastError) {
        // Content script not loaded — inject it first
        chrome.scripting.executeScript(
          { target: { tabId }, files: ['content.js'] },
          () => {
            chrome.tabs.sendMessage(tabId, { action: 'extractJD' }, (retryResponse) => {
              sendResponse(retryResponse || { error: 'Could not extract JD' });
            });
          }
        );
      } else {
        sendResponse(response);
      }
    });
    return true; // async response
  }
});

// Log extension install/update
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('GitPulse extension installed');
  } else if (details.reason === 'update') {
    console.log('GitPulse extension updated to', chrome.runtime.getManifest().version);
  }
});
