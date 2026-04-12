import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { GitBranch, BookOpen, Loader2 } from 'lucide-react';
import { getInterviewPrep } from '../services/api';
import InterviewCard from '../components/InterviewCard';

export default function InterviewPrep() {
  const [params] = useSearchParams();
  const [username, setUsername] = useState(params.get('username') || '');
  const [jdText, setJdText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('technical');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !jdText) return;
    setLoading(true);
    try {
      const res = await getInterviewPrep(username, jdText);
      setResult(res.data);
    } catch (err) { /* handled by UI */ }
    setLoading(false);
  };

  const prep = result?.prep;
  const tabs = [
    { key: 'technical', label: 'Technical', count: prep?.technical_questions?.length },
    { key: 'behavioral', label: 'Behavioral', count: prep?.behavioral_questions?.length },
    { key: 'coding', label: 'Coding', count: prep?.coding_challenges?.length },
    { key: 'gap', label: 'Gap Coverage', count: prep?.gap_coverage_questions?.length },
  ];

  const questions = prep ? {
    technical: prep.technical_questions || [],
    behavioral: prep.behavioral_questions || [],
    coding: prep.coding_challenges || [],
    gap: prep.gap_coverage_questions || [],
  } : {};

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <span className="text-text-muted text-sm">Interview Prep</span>
      </nav>
      <div className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-text-primary mb-6 flex items-center gap-2"><BookOpen size={24} /> Interview Prep</h1>
        <form onSubmit={handleSubmit} className="space-y-4 mb-8">
          <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="GitHub username"
            className="w-full px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent" />
          <textarea value={jdText} onChange={(e) => setJdText(e.target.value)} placeholder="Paste job description..."
            rows={5} className="w-full px-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent resize-y" />
          <button type="submit" disabled={loading || !username || !jdText}
            className="px-5 py-2 rounded-lg bg-accent hover:bg-accent-dark text-white text-sm disabled:opacity-50 flex items-center gap-2">
            {loading ? <><Loader2 size={14} className="animate-spin" /> Generating...</> : 'Generate Prep'}
          </button>
        </form>

        {prep && (
          <div>
            <div className="flex gap-1 mb-4 border-b border-border">
              {tabs.map((t) => (
                <button key={t.key} onClick={() => setTab(t.key)}
                  className={`px-3 py-2 text-sm border-b-2 transition-colors ${tab === t.key ? 'border-accent text-accent' : 'border-transparent text-text-muted hover:text-text-secondary'}`}>
                  {t.label} {t.count > 0 && <span className="text-xs">({t.count})</span>}
                </button>
              ))}
            </div>
            <div className="space-y-3">
              {(questions[tab] || []).map((q, i) => <InterviewCard key={i} question={q} type={tab} />)}
              {(questions[tab] || []).length === 0 && <p className="text-text-muted text-sm">No questions in this category.</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
