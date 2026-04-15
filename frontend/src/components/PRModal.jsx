import { useState } from 'react';
import api from '../services/api';

export default function PRModal({ isOpen, onClose, repoName, readmeContent, username }) {
  const [token, setToken] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (!token.trim() || !confirmed) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/pr/open', {
        username,
        repo_name: repoName,
        new_readme_content: readmeContent,
        token: token.trim()
      }, { timeout: 60000 });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to open PR');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setToken('');
    setConfirmed(false);
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-bg-secondary border border-border rounded-lg max-w-lg w-full p-6 max-h-[90vh] overflow-y-auto">
        {!result ? (
          <>
            <h3 className="text-xl font-semibold text-text-primary mb-2">
              Open Pull Request on {repoName}
            </h3>
            <p className="text-text-muted text-sm mb-4">
              GitPulse will create a new branch on your repo, commit the improved README, and open a PR for your review. You can merge or close it from GitHub.
            </p>

            <div className="bg-bg-tertiary rounded p-3 mb-4 text-sm text-text-secondary">
              <p className="font-medium text-text-primary mb-2">You need a GitHub Personal Access Token with repo scope.</p>
              <a
                href="https://github.com/settings/tokens/new?scopes=repo&description=GitPulse%20PR%20Agent"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent-light hover:text-accent underline text-xs"
              >
                Generate token on GitHub
              </a>
            </div>

            <label className="block text-sm text-text-secondary mb-2">GitHub Token</label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="ghp_..."
              className="w-full bg-bg-tertiary border border-border rounded px-3 py-2 text-text-primary text-sm font-mono mb-4 outline-none focus:border-accent"
              autoComplete="off"
            />

            <label className="flex items-start gap-2 text-xs text-text-muted mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="mt-0.5"
              />
              <span>
                I understand my token is sent to the GitPulse backend only for this single PR operation and is not stored anywhere. Source code:{' '}
                <a href="https://github.com/tarundattagondi/GitPulse/blob/main/backend/services/pr_agent.py" target="_blank" rel="noopener noreferrer" className="text-accent-light underline">pr_agent.py</a>
              </span>
            </label>

            {error && (
              <div className="bg-danger/10 border border-danger/20 rounded p-3 mb-4 text-sm text-danger">
                {error}
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={handleClose}
                className="px-4 py-2 text-text-muted hover:text-text-primary text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={!token.trim() || !confirmed || loading}
                className="px-4 py-2 bg-accent hover:bg-accent-dark disabled:bg-bg-tertiary disabled:cursor-not-allowed text-white rounded font-medium text-sm"
              >
                {loading ? 'Opening PR...' : 'Open Pull Request'}
              </button>
            </div>
          </>
        ) : (
          <div className="text-center py-4">
            <div className="text-5xl mb-3 text-success">&#10003;</div>
            <h3 className="text-xl font-semibold text-text-primary mb-2">Pull Request Created</h3>
            <p className="text-text-secondary text-sm mb-1">PR #{result.pr_number} on {repoName}</p>
            <p className="text-text-muted text-xs mb-6">Branch: {result.branch_name}</p>

            <a
              href={result.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-6 py-3 bg-accent hover:bg-accent-dark text-white rounded font-medium mb-3"
            >
              View PR on GitHub
            </a>

            <div>
              <button
                onClick={handleClose}
                className="text-text-muted hover:text-text-primary text-sm"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
