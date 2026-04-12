// Content script: extracts job description text from supported job sites.
// Auto-injected on matched hosts via manifest.json content_scripts.
// Also responds to messages from popup.js.

function extractJD() {
  const hostname = window.location.hostname;

  // LinkedIn
  if (hostname.includes('linkedin.com')) {
    try {
      const selectors = [
        '.jobs-description__content',
        '.jobs-box__html-content',
        '.description__text',
        '[class*="job-details"]',
        '.jobs-description',
      ];
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el?.innerText?.length > 50) return el.innerText;
      }
    } catch (e) { /* fall through */ }
  }

  // Greenhouse
  if (hostname.includes('greenhouse.io')) {
    try {
      const selectors = [
        '#content',
        '.content',
        '#app_body',
        '[data-qa="job-description"]',
        '.job-post',
      ];
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el?.innerText?.length > 50) return el.innerText;
      }
    } catch (e) { /* fall through */ }
  }

  // Lever
  if (hostname.includes('lever.co')) {
    try {
      const selectors = [
        '.section-wrapper',
        '.content',
        '[data-qa="job-description"]',
        '.posting-page',
      ];
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el?.innerText?.length > 50) return el.innerText;
      }
    } catch (e) { /* fall through */ }
  }

  // Ashby
  if (hostname.includes('ashbyhq.com')) {
    try {
      const selectors = [
        '[data-testid="job-posting"]',
        '.ashby-job-posting-description',
        'main',
        '.job-posting',
      ];
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el?.innerText?.length > 50) return el.innerText;
      }
    } catch (e) { /* fall through */ }
  }

  // Generic fallback
  try {
    const genericSelectors = [
      '[class*="description"]',
      '[class*="job-detail"]',
      '[class*="posting"]',
      'article',
      'main',
      '[role="main"]',
    ];
    for (const sel of genericSelectors) {
      const el = document.querySelector(sel);
      if (el?.innerText?.length > 100) return el.innerText;
    }
  } catch (e) { /* fall through */ }

  // Last resort: body text
  const bodyText = document.body?.innerText || '';
  if (bodyText.length > 200) {
    return bodyText.substring(0, 8000);
  }

  return null;
}

// Message listener for popup.js
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_JD') {
    sendResponse({ jd: extractJD() });
  }
  return true; // keep channel open for async
});
