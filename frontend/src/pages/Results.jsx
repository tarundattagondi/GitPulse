import { useLocation, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { GitBranch, ArrowLeft, Loader2, CheckCircle, XCircle, Star, Code, ChevronDown, ChevronUp, Calendar, Lightbulb, BookOpen } from 'lucide-react';
import { getLatestAnalysis, analyzeProfile } from '../services/api';
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
    if (data) return;
    const u = searchParams.get('username');
    if (!u) return;
    setUsername(u);
    setLoading(true);

    getLatestAnalysis(u)
      .then((res) => { setData(res.data); setLoading(false); })
      .catch((err) => {
        if (err.message?.includes('404') || err.message?.includes('No analysis found')) {
          // Run a fresh analysis
          return analyzeProfile(u).then((res) => { setData(res.data); setLoading(false); });
        }
        throw err;
      })
      .catch((err) => { setError(err.message || 'Failed to load'); setLoading(false); });
  }, [searchParams, data]);

  if (loading) return <FullScreenMsg><Loader2 size={32} className="text-accent animate-spin mx-auto mb-3" /><p className="text-text-muted">Loading analysis for {username}...</p></FullScreenMsg>;
  if (error) return <FullScreenMsg><p className="text-danger mb-4">{error}</p><button onClick={() => navigate('/')} className="px-4 py-2 bg-accent text-white rounded-lg text-sm">Go home</button></FullScreenMsg>;
  if (!data) return <FullScreenMsg><p className="text-text-muted mb-4">No results to display</p><button onClick={() => navigate('/')} className="px-4 py-2 bg-accent text-white rounded-lg text-sm">Go home</button></FullScreenMsg>;

  const profile = data.profile || data.github_summary?.profile || {};
  const score = data.score || {};
  const repoCount = data.repos_count || data.github_summary?.repo_count || 0;
  const totalStars = data.github_summary?.total_stars || 0;
  const overallScore = data.overall_score || score.total_score || 0;
  const categoryScores = data.category_scores || {};
  const jdAnalysis = data.jd_analysis;
  const matchResult = data.match_result;
  const recs = data.recommendations;
  const repos = data.github_summary?.repos || [];
  const priorityActions = recs?.priority_actions || [];

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <button onClick={() => navigate('/')} className="flex items-center gap-1 text-sm text-text-muted hover:text-text-primary"><ArrowLeft size={16} /> Back</button>
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <div className="w-16" />
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center gap-4">
          {profile.avatar_url && <img src={profile.avatar_url} alt="" className="w-16 h-16 rounded-full border-2 border-accent/30" />}
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{profile.name || username}</h1>
            <p className="text-text-muted text-sm">{repoCount} repos · {totalStars} stars</p>
          </div>
        </div>

        {/* Score + Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex justify-center relative">
            <MatchGauge score={overallScore} label="Overall Score" />
          </div>
          <div className="md:col-span-2 p-4 rounded-lg bg-bg-secondary border border-border">
            <h3 className="text-sm font-medium text-text-primary mb-3">Score Breakdown</h3>
            <ScoreBreakdown breakdown={score.breakdown || categoryScores} />
          </div>
        </div>

        {/* Quick links */}
        <div className="flex flex-wrap gap-3">
          <Link to="/jobs" className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Browse Jobs</Link>
          <Link to={`/benchmarks?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Company Benchmarks</Link>
          <Link to={`/interview-prep?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Interview Prep</Link>
          <Link to={`/tri-match?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Tri-Source Match</Link>
          <Link to={`/history?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border hover:border-accent/50 text-sm text-text-secondary">Progress History</Link>
        </div>

        {/* JD Analysis */}
        {jdAnalysis && <JDAnalysisSection jd={jdAnalysis} />}

        {/* Match Breakdown */}
        {matchResult && <MatchBreakdownSection match={matchResult} />}

        {/* Recommendations */}
        {recs && <RecommendationsSection recs={recs} />}

        {/* Repos */}
        {repos.length > 0 && (
          <Section title="Repositories">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {repos.slice(0, 8).map((r) => (
                <a key={r.name} href={r.html_url} target="_blank" rel="noopener noreferrer"
                  className="p-3 rounded-lg bg-bg-tertiary border border-border hover:border-accent/50 transition-colors">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-medium text-text-primary">{r.name}</span>
                    <span className="flex items-center gap-1 text-xs text-text-muted"><Star size={10} /> {r.stars || 0}</span>
                  </div>
                  <p className="text-xs text-text-muted mt-1 line-clamp-2">{r.description || 'No description'}</p>
                  {r.language && <span className="inline-flex items-center gap-1 text-xs text-accent-light mt-2"><Code size={10} /> {r.language}</span>}
                </a>
              ))}
            </div>
          </Section>
        )}

        {/* Share */}
        <ShareCard username={username} score={overallScore} actions={priorityActions.slice(0, 3)} />
      </div>
    </div>
  );
}

function FullScreenMsg({ children }) {
  return <div className="min-h-screen flex items-center justify-center"><div className="text-center">{children}</div></div>;
}

function Section({ title, children }) {
  return (
    <div className="rounded-lg bg-bg-secondary border border-border p-6">
      <h2 className="text-lg font-semibold text-text-primary mb-4">{title}</h2>
      {children}
    </div>
  );
}

function Pill({ children, color = 'accent' }) {
  const colors = {
    accent: 'bg-accent/10 text-accent-light border-accent/20',
    success: 'bg-success/10 text-success border-success/20',
    danger: 'bg-danger/10 text-danger border-danger/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    muted: 'bg-bg-tertiary text-text-muted border-border',
  };
  return <span className={`px-2 py-0.5 text-xs rounded-full border ${colors[color]}`}>{children}</span>;
}

function JDAnalysisSection({ jd }) {
  return (
    <Section title="Job Description Analysis">
      <div className="space-y-4">
        <div className="flex items-center gap-3 text-sm">
          <Pill color="accent">{jd.role_category || 'other'}</Pill>
          <Pill color="muted">{jd.experience_level || 'unknown'}</Pill>
          {jd.company_industry && <Pill color="muted">{jd.company_industry}</Pill>}
        </div>
        {(jd.required_skills?.length > 0) && (
          <div>
            <h4 className="text-xs font-medium text-text-secondary mb-2">Required Skills</h4>
            <div className="flex flex-wrap gap-1.5">{jd.required_skills.map((s) => <Pill key={s} color="danger">{s}</Pill>)}</div>
          </div>
        )}
        {(jd.preferred_skills?.length > 0) && (
          <div>
            <h4 className="text-xs font-medium text-text-secondary mb-2">Preferred Skills</h4>
            <div className="flex flex-wrap gap-1.5">{jd.preferred_skills.map((s) => <Pill key={s} color="warning">{s}</Pill>)}</div>
          </div>
        )}
        {(jd.tools?.length > 0) && (
          <div>
            <h4 className="text-xs font-medium text-text-secondary mb-2">Tools & Technologies</h4>
            <div className="flex flex-wrap gap-1.5">{jd.tools.map((s) => <Pill key={s} color="muted">{s}</Pill>)}</div>
          </div>
        )}
      </div>
    </Section>
  );
}

function MatchBreakdownSection({ match }) {
  const catScores = match.category_scores || {};
  const allFound = [];
  const allMissing = [];
  Object.values(catScores).forEach((c) => {
    allFound.push(...(c.found || []));
    allMissing.push(...(c.missing || []));
  });
  const relevantRepos = match.most_relevant_repos || [];
  const gaps = match.gap_items || [];
  const strengths = match.strengths_for_role || [];

  return (
    <Section title="Match Breakdown">
      <div className="space-y-4">
        {match.overall_match_pct != null && (
          <p className="text-sm text-text-secondary">Overall match: <span className="font-bold text-accent">{match.overall_match_pct}%</span></p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-xs font-medium text-success mb-2 flex items-center gap-1"><CheckCircle size={12} /> Skills Found ({allFound.length})</h4>
            <div className="flex flex-wrap gap-1.5">{allFound.map((s) => <Pill key={s} color="success">{s}</Pill>)}</div>
          </div>
          <div>
            <h4 className="text-xs font-medium text-danger mb-2 flex items-center gap-1"><XCircle size={12} /> Skills Missing ({allMissing.length})</h4>
            <div className="flex flex-wrap gap-1.5">{allMissing.map((s) => <Pill key={s} color="danger">{s}</Pill>)}</div>
          </div>
        </div>
        {relevantRepos.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-text-secondary mb-2">Most Relevant Repos</h4>
            <div className="flex flex-wrap gap-1.5">{relevantRepos.map((r) => <Pill key={r} color="accent">{r}</Pill>)}</div>
          </div>
        )}
        {gaps.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-warning mb-2">Key Gaps</h4>
            <ul className="space-y-1">{gaps.map((g, i) => <li key={i} className="text-xs text-text-muted">• {g}</li>)}</ul>
          </div>
        )}
        {strengths.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-success mb-2">Strengths for Role</h4>
            <ul className="space-y-1">{strengths.map((s, i) => <li key={i} className="text-xs text-text-muted">• {s}</li>)}</ul>
          </div>
        )}
      </div>
    </Section>
  );
}

function RecommendationsSection({ recs }) {
  const actions = recs.priority_actions || [];
  const projects = recs.missing_projects || [];
  const rewrites = recs.readme_rewrites || [];
  const plan = recs.thirty_day_plan || {};
  const interviewTopics = recs.interview_prep_topics || [];

  return (
    <Section title="Recommendations">
      <div className="space-y-6">
        {/* Priority Actions */}
        {actions.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-warning mb-2 flex items-center gap-1"><Lightbulb size={14} /> Priority Actions</h3>
            <ol className="space-y-2">
              {actions.map((a, i) => (
                <li key={i} className="flex gap-2 text-sm text-text-secondary">
                  <span className="text-accent font-bold shrink-0">{i + 1}.</span> {a}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Missing Projects */}
        {projects.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-accent-light mb-2">Projects to Build</h3>
            <div className="space-y-3">
              {projects.map((p, i) => (
                <div key={i} className="p-3 rounded-lg bg-bg-tertiary border border-border">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-medium text-text-primary">{p.name}</span>
                    {p.estimated_hours && <span className="text-xs text-text-muted">~{p.estimated_hours}h</span>}
                  </div>
                  <p className="text-xs text-text-muted mt-1">{p.description}</p>
                  {p.skills_demonstrated?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">{p.skills_demonstrated.map((s) => <Pill key={s} color="accent">{s}</Pill>)}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* README Rewrites */}
        {rewrites.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-accent-light mb-2">README Improvements</h3>
            <div className="space-y-2">
              {rewrites.map((rw, i) => <ExpandableReadme key={i} rewrite={rw} />)}
            </div>
          </div>
        )}

        {/* 30-Day Plan */}
        {Object.keys(plan).length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-accent-light mb-2 flex items-center gap-1"><Calendar size={14} /> 30-Day Improvement Plan</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(plan).map(([week, info]) => (
                <div key={week} className="p-3 rounded-lg bg-bg-tertiary border border-border">
                  <h4 className="text-xs font-medium text-accent capitalize">{week.replace('_', ' ')}</h4>
                  <p className="text-xs text-text-muted mt-1">{info?.focus || ''}</p>
                  <ul className="mt-2 space-y-1">
                    {(info?.tasks || []).slice(0, 3).map((t, j) => (
                      <li key={j} className="text-xs text-text-secondary flex gap-1"><span className="text-warning shrink-0">•</span> {t}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Interview Prep Topics */}
        {interviewTopics.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-accent-light mb-2 flex items-center gap-1"><BookOpen size={14} /> Interview Prep Topics</h3>
            <div className="space-y-2">
              {interviewTopics.map((t, i) => {
                const topic = typeof t === 'string' ? t : t.topic;
                const why = typeof t === 'object' ? t.why : null;
                return (
                  <div key={i} className="p-2 rounded bg-bg-tertiary text-sm">
                    <span className="text-text-primary">{topic}</span>
                    {why && <p className="text-xs text-text-muted mt-0.5">{why}</p>}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Section>
  );
}

function ExpandableReadme({ rewrite }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg bg-bg-tertiary border border-border">
      <button onClick={() => setOpen(!open)} className="w-full p-3 flex justify-between items-center text-left">
        <span className="text-sm text-text-primary">{rewrite.repo}</span>
        <span className="text-text-muted">{open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 border-t border-border pt-2">
          <pre className="text-xs text-text-muted whitespace-pre-wrap font-mono max-h-64 overflow-auto">{rewrite.readme_content}</pre>
        </div>
      )}
    </div>
  );
}
