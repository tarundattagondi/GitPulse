import { useLocation, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { GitBranch, ArrowLeft, Loader2 } from 'lucide-react';
import { analyzeProfile, getProgress } from '../services/api';
import MatchGauge from '../components/MatchGauge';
import ScoreBreakdown from '../components/ScoreBreakdown';
import ShareCard from '../components/ShareCard';

export default function Results() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [data, setData] = useState(state?.data || null);
  const [username, setUsername] = useState(state?.username || searchParams.get('username') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // If we already have data from navigation state, don't fetch
    if (data) return;

    const usernameParam = searchParams.get('username');
    if (!usernameParam) return;

    setUsername(usernameParam);
    setLoading(true);

    // Try progress endpoint first for the latest snapshot
    getProgress(usernameParam)
      .then((res) => {
        const snapshots = res.data?.snapshots || [];
        if (snapshots.length > 0) {
          const latest = snapshots[snapshots.length - 1];
          setData({
            profile: { login: usernameParam, name: usernameParam, html_url: `https://github.com/${usernameParam}` },
            repos_count: latest.repo_count || 0,
            score: {
              total_score: latest.overall_score,
              breakdown: latest.category_scores,
            },
            snapshot: latest,
          });
          setLoading(false);
          return;
        }
        // No snapshots — run a fresh analysis
        return analyzeProfile(usernameParam).then((res) => {
          setData(res.data);
          setLoading(false);
        });
      })
      .catch((err) => {
        setError(err.message || 'Failed to load analysis');
        setLoading(false);
      });
  }, [searchParams, data]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 size={32} className="text-accent animate-spin mx-auto mb-3" />
          <p className="text-text-muted">Loading analysis for {username}...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-danger mb-4">{error}</p>
          <button onClick={() => navigate('/')} className="px-4 py-2 bg-accent text-white rounded-lg text-sm">Go home</button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-muted mb-4">No results to display</p>
          <button onClick={() => navigate('/')} className="px-4 py-2 bg-accent text-white rounded-lg text-sm">Go home</button>
        </div>
      </div>
    );
  }

  const { profile, score, repos_count } = data;

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <button onClick={() => navigate('/')} className="flex items-center gap-1 text-sm text-text-muted hover:text-text-primary">
          <ArrowLeft size={16} /> Back
        </button>
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <div className="w-16" />
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        <div className="flex items-center gap-4">
          {profile.avatar_url && <img src={profile.avatar_url} alt="" className="w-16 h-16 rounded-full border-2 border-accent/30" />}
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{profile.name || username}</h1>
            <p className="text-text-muted text-sm">{profile.bio || `${repos_count} repos`}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex justify-center relative">
            <MatchGauge score={score.total_score} label="Overall Score" />
          </div>
          <div className="md:col-span-2 p-4 rounded-lg bg-bg-secondary border border-border">
            <h3 className="text-sm font-medium text-text-primary mb-3">Score Breakdown</h3>
            <ScoreBreakdown breakdown={score.breakdown} />
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link to={`/jobs`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Browse Jobs</Link>
          <Link to={`/benchmarks?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Company Benchmarks</Link>
          <Link to={`/interview-prep?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Interview Prep</Link>
          <Link to={`/tri-match?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Tri-Source Match</Link>
          <Link to={`/history?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Progress History</Link>
        </div>

        <ShareCard username={username} score={score.total_score} />
      </div>
    </div>
  );
}
