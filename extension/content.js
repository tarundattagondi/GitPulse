// Content script: extracts job description text from supported job sites.
// Each site has specific selectors with fallback to generic extraction.

function extractJDText() {
  const hostname = window.location.hostname;

  // LinkedIn
  if (hostname.includes('linkedin.com')) {
    try {
      // Try multiple LinkedIn selectors (layout changes frequently)
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

  // Generic fallback: try common job description containers
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

  // Last resort: grab the body text
  const bodyText = document.body?.innerText || '';
  if (bodyText.length > 200) {
    return bodyText.substring(0, 8000);
  }

  return null;
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractJD') {
    const jdText = extractJDText();
    sendResponse({ jdText });
  }
  return true; // keep channel open for async
});
