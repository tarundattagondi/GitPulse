import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { GitBranch, Upload, Loader2 } from 'lucide-react';
import { triMatch } from '../services/api';
import SkillsGapChart from '../components/SkillsGapChart';

export default function TriMatch() {
  const [params] = useSearchParams();
  const [username, setUsername] = useState(params.get('username') || '');
  const [jdText, setJdText] = useState('');
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !jdText || !file) return;
    setLoading(true); setError(null);
    const fd = new FormData();
    fd.append('github_username', username);
    fd.append('jd_text', jdText);
    fd.append('resume', file);
    try {
      const res = await triMatch(fd);
      setResult(res.data);
    } catch (err) { setError(err.message); }
    setLoading(false);
  };

  const r = result?.match_result;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <span className="text-text-muted text-sm">Tri-Source Match</span>
      </nav>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-text-primary mb-6">Tri-Source Match</h1>
        <form onSubmit={handleSubmit} className="space-y-4 mb-8">
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="GitHub username"
            className="w-full px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent" />
          <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} placeholder="Paste job description..."
            rows={6} className="w-full px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent resize-y" />
          <label className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-secondary border border-border text-sm text-text-secondary cursor-pointer hover:border-accent/50">
            <Upload size={14} /> {file ? file.name : 'Upload resume (PDF, DOCX, TXT)'}
            <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files[0])} className="hidden" />
          </label>
          <button type="submit" disabled={loading || !username || !jdText || !file}
            className="px-5 py-2 rounded-lg bg-accent hover:bg-accent-dark text-white text-sm disabled:opacity-50 flex items-center gap-2">
            {loading ? <><Loader2 size={14} className="animate-spin" /> Analyzing...</> : 'Run Tri-Match'}
          </button>
          {error && <p className="text-danger text-sm">{error}</p>}
        </form>

        {r && (
          <div className="space-y-6">
            {r.resume_says_github_doesnt_prove?.length > 0 && (
              <Section title="Resume Claims GitHub Doesn't Prove" color="text-warning">
                {r.resume_says_github_doesnt_prove.map((item, i) => (
                  <div key={i} className="p-3 rounded bg-bg-tertiary text-sm">
                    <p className="text-text-primary">{item.claim}</p>
                    <p className="text-text-muted text-xs mt-1">Missing: {item.evidence_missing}</p>
                  </div>
                ))}
              </Section>
            )}
            {r.github_shows_resume_doesnt_mention?.length > 0 && (
              <Section title="GitHub Shows, Resume Doesn't Mention" color="text-accent-light">
                {r.github_shows_resume_doesnt_mention.map((item, i) => (
                  <div key={i} className="p-3 rounded bg-bg-tertiary text-sm">
                    <p className="text-text-primary">{item.github_evidence}</p>
                    <p className="text-text-muted text-xs mt-1">Add: {item.suggestion}</p>
                  </div>
                ))}
              </Section>
            )}
            {r.both_missing_for_jd?.length > 0 && (
              <Section title="Both Missing for JD" color="text-danger">
                {r.both_missing_for_jd.map((item, i) => (
                  <div key={i} className="p-3 rounded bg-bg-tertiary text-sm flex justify-between">
                    <span className="text-text-primary">{item.requirement}</span>
                    <span className="text-xs text-text-muted">{item.importance}</span>
                  </div>
                ))}
              </Section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, color, children }) {
  return (
    <div className="p-4 rounded-lg bg-bg-secondary border border-border">
      <h3 className={`text-sm font-medium ${color} mb-3`}>{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  );
}
