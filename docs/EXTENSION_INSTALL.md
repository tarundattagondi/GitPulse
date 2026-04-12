# GitPulse Chrome Extension — Installation Guide

## Prerequisites

- Google Chrome (version 88+)
- GitPulse backend running (locally or deployed)

## Installation Steps

1. **Open Chrome Extensions page**
   - Navigate to `chrome://extensions` in your Chrome browser
   - Or go to Menu (three dots) > Extensions > Manage Extensions

2. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top-right corner

3. **Load the extension**
   - Click "Load unpacked"
   - Navigate to the `extension/` folder inside the GitPulse project
   - Select the folder and click "Open"

4. **Pin the extension**
   - Click the puzzle piece icon in the Chrome toolbar
   - Find "GitPulse — Job Match Scorer"
   - Click the pin icon to keep it visible

## Usage

1. Navigate to a job listing on:
   - LinkedIn Jobs (`linkedin.com/jobs/*`)
   - Greenhouse (`boards.greenhouse.io/*`)
   - Lever (`jobs.lever.co/*`)
   - Ashby (`jobs.ashbyhq.com/*`)

2. Click the GitPulse extension icon in your toolbar

3. Enter your GitHub username (saved for next time)

4. Click "Score This Job"

5. View your match score, prep questions, and gap analysis

## Configuration

By default, the extension connects to `https://gitpulse-api.up.railway.app`. To use a local backend:

1. Open `extension/popup.js`
2. Change the `API_BASE` constant to `http://localhost:8000`
3. Reload the extension on `chrome://extensions`

## Troubleshooting

- **"Could not extract job description"** — The page may not have loaded fully. Wait a moment and try again, or try a different job listing.
- **API errors** — Make sure the GitPulse backend is running and accessible.
- **Extension not working after update** — Click the refresh icon on `chrome://extensions` to reload.
