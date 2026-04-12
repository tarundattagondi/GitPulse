const API_BASE = 'https://web-production-c8290.up.railway.app';

const $ = (id) => document.getElementById(id);

document.addEventListener('DOMContentLoaded', async () => {
  const stored = await chrome.storage.local.get('gitpulse_username');
  if (stored.gitpulse_username) {
    $('username').value = stored.gitpulse_username;
  }
  $('score-btn').addEventListener('click', handleScore);
});

// ── Progress stepper ────────────────────────────────────────────

function advanceStep(n) {
  document.querySelectorAll('.step').forEach((el) => {
    const step = parseInt(el.dataset.step);
    el.classList.remove('active', 'done');
    if (step < n) el.classList.add('done');
    else if (step === n) el.classList.add('active');
  });
}

function completeAllSteps() {
  document.querySelectorAll('.step').forEach((el) => {
    el.classList.remove('active');
    el.classList.add('done');
  });
}

// ── Main handler ────────────────────────────────────────────────

async function handleScore() {
  const username = $('username').value.trim();
  if (!username) {
    showError('Enter your GitHub username.');
    return;
  }

  await chrome.storage.local.set({ gitpulse_username: username });

  // Reset UI
  $('score-btn').disabled = true;
  $('result').classList.add('hidden');
  $('error-box').classList.add('hidden');
  $('progress').classList.remove('hidden');

  // Step 1: Extract JD
  advanceStep(1);

  let jdText = null;
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error('No active tab found.');

    // Try content script first
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_JD' });
      jdText = response?.jd;
    } catch {
      // Content script not present
    }

    // Fallback: scripting API
    if (!jdText) {
      const [{ result }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.body.innerText,
      });
      jdText = result;
    }

    if (!jdText || jdText.length < 50) {
      throw new Error(
        'Could not extract job description. Try a job listing on LinkedIn, Greenhouse, Lever, or Ashby.'
      );
    }
  } catch (err) {
    showError(err.message);
    return;
  }

  // Steps 2-5: simulated progression while real API call runs
  const timers = [
    setTimeout(() => advanceStep(2), 500),
    setTimeout(() => advanceStep(3), 5000),
    setTimeout(() => advanceStep(4), 15000),
    setTimeout(() => advanceStep(5), 25000),
  ];

  // API call with 60s timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 60000);

  try {
    const url = `${API_BASE}/api/analyze/${username}?role_category=other`;
    console.log('GitPulse POST:', url);

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jd_text: jdText.substring(0, 5000) }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    console.log('GitPulse status:', res.status);

    if (!res.ok) {
      const errText = await res.text();
      console.error('GitPulse error response:', errText);
      let errMsg;
      try { errMsg = JSON.parse(errText).message; } catch { errMsg = errText; }
      throw new Error(`Backend ${res.status}: ${errMsg}`);
    }

    const data = await res.json();
    console.log('GitPulse response:', JSON.stringify(data).substring(0, 200));

    // Mark all steps done, then show result
    timers.forEach(clearTimeout);
    completeAllSteps();
    setTimeout(() => showResult(data, username), 400);

  } catch (err) {
    clearTimeout(timeoutId);
    timers.forEach(clearTimeout);

    if (err.name === 'AbortError') {
      showError('Request timed out after 60 seconds. The backend may be slow — try again.');
    } else {
      showError(err.message);
    }
  } finally {
    $('score-btn').disabled = false;
  }
}

// ── Result display ──────────────────────────────────────────────

function showResult(data, username) {
  $('progress').classList.add('hidden');

  const result = $('result');
  result.classList.remove('hidden');

  // Overall score from /api/analyze response
  const score = Math.round(data.overall_score || 0);
  result.querySelector('.score-display').textContent = score + '/100';
  result.querySelector('.score-display').style.color =
    score >= 70 ? '#4ade80' : score >= 40 ? '#fbbf24' : '#f87171';

  // Category breakdown bars — real GitPulse scoring categories
  const categories = data.category_scores || {};
  const labels = {
    skills_match: { name: 'Skills Match', max: 40 },
    project_relevance: { name: 'Project Relevance', max: 25 },
    readme_quality: { name: 'README Quality', max: 15 },
    activity_level: { name: 'Activity Level', max: 10 },
    profile_completeness: { name: 'Profile Completeness', max: 10 },
  };

  const breakdown = $('breakdown');
  breakdown.innerHTML = '';
  Object.entries(labels).forEach(([key, { name, max }]) => {
    const val = Math.round(categories[key] || 0);
    const pct = Math.round((val / max) * 100);
    const level = pct >= 70 ? 'high' : pct >= 40 ? 'mid' : 'low';
    breakdown.innerHTML += `
      <div class="bar-row">
        <span class="bar-label">${name}</span>
        <div class="bar-track"><div class="bar-fill ${level}" style="width:${pct}%"></div></div>
        <span class="bar-score">${val}/${max}</span>
      </div>`;
  });

  // Summary line
  result.querySelector('.summary').textContent =
    `${data.repos_count || 0} repos analyzed · ${Object.keys(categories).length} categories scored`;

  // Hide interview-prep sections (not applicable for analyze response)
  $('gaps').classList.add('hidden');
  $('strengths').classList.add('hidden');

  // View full report button
  $('view-full').onclick = () => {
    chrome.tabs.create({ url: `https://git-pulse-ten.vercel.app/results?username=${username}` });
  };
}

// ── Error display ───────────────────────────────────────────────

function showError(msg) {
  $('progress').classList.add('hidden');
  $('result').classList.add('hidden');
  const errorBox = $('error-box');
  errorBox.textContent = msg;
  errorBox.classList.remove('hidden');
  $('score-btn').disabled = false;
}
