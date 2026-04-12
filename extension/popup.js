// Replace with your deployed backend URL
const API_BASE = 'https://gitpulse-api.up.railway.app';

const $ = (id) => document.getElementById(id);

document.addEventListener('DOMContentLoaded', async () => {
  // Restore saved username
  const stored = await chrome.storage.local.get('gitpulse_username');
  if (stored.gitpulse_username) {
    $('username').value = stored.gitpulse_username;
  }

  $('scoreBtn').addEventListener('click', handleScore);
});

async function handleScore() {
  const username = $('username').value.trim();
  if (!username) {
    showStatus('Enter your GitHub username.', 'error');
    return;
  }

  // Save username
  await chrome.storage.local.set({ gitpulse_username: username });

  // Disable button
  $('scoreBtn').disabled = true;
  $('results').classList.add('hidden');
  showStatus('Extracting job description from page...', 'loading');

  try {
    // Get JD text from content script
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) throw new Error('No active tab found.');

    let jdText;
    try {
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'extractJD' });
      jdText = response?.jdText;
    } catch {
      // Content script not injected — try injecting it
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
      const response = await chrome.tabs.sendMessage(tab.id, { action: 'extractJD' });
      jdText = response?.jdText;
    }

    if (!jdText || jdText.length < 50) {
      throw new Error('Could not extract job description from this page. Try a job listing page on LinkedIn, Greenhouse, Lever, or Ashby.');
    }

    showStatus(`Scoring ${username} against this JD...`, 'loading');

    // Call GitPulse backend
    const res = await fetch(`${API_BASE}/api/interview-prep`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, jd_text: jdText.substring(0, 5000) }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `API error: ${res.status}`);
    }

    const data = await res.json();
    showResults(data);
    showStatus('Analysis complete!', 'success');

  } catch (err) {
    showStatus(err.message, 'error');
  } finally {
    $('scoreBtn').disabled = false;
  }
}

function showStatus(msg, type) {
  const el = $('status');
  el.textContent = msg;
  el.className = `status ${type}`;
  el.classList.remove('hidden');
}

function showResults(data) {
  const results = $('results');
  results.classList.remove('hidden');

  // Overall match
  const score = data.overall_match_pct || 0;
  $('scoreValue').textContent = score;
  $('scoreValue').style.color = score >= 75 ? '#22c55e' : score >= 50 ? '#eab308' : '#ef4444';

  // Breakdown from prep data
  const breakdown = $('breakdown');
  breakdown.innerHTML = '';
  const prep = data.prep || {};

  const categories = [
    { label: 'Technical Qs', count: (prep.technical_questions || []).length, max: 7 },
    { label: 'Behavioral Qs', count: (prep.behavioral_questions || []).length, max: 5 },
    { label: 'Coding Challenges', count: (prep.coding_challenges || []).length, max: 5 },
    { label: 'Gap Areas', count: (prep.gap_coverage_questions || []).length, max: 4 },
  ];

  categories.forEach(({ label, count, max }) => {
    const pct = Math.round((count / max) * 100);
    const level = pct >= 70 ? 'high' : pct >= 40 ? 'mid' : 'low';
    breakdown.innerHTML += `
      <div class="bar-row">
        <span class="bar-label">${label}</span>
        <div class="bar-track"><div class="bar-fill ${level}" style="width:${pct}%"></div></div>
        <span class="bar-score">${count}</span>
      </div>`;
  });

  // Gaps
  const gapItems = prep.gap_coverage_questions || [];
  if (gapItems.length > 0) {
    $('gaps').classList.remove('hidden');
    $('gapList').innerHTML = gapItems.map((g) => `<li>${g.gap || g.question}</li>`).join('');
  } else {
    $('gaps').classList.add('hidden');
  }

  // Strengths — pull from technical questions skill_tested
  const skills = (prep.technical_questions || []).map((q) => q.skill_tested).filter(Boolean).slice(0, 5);
  if (skills.length > 0) {
    $('strengths').classList.remove('hidden');
    $('strengthList').innerHTML = skills.map((s) => `<li>${s}</li>`).join('');
  } else {
    $('strengths').classList.add('hidden');
  }
}
