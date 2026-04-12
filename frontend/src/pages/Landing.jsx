import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GitBranch, Search, BarChart3, Briefcase, FileText, Target } from 'lucide-react';

export default function Landing() {
  const [username, setUsername] = useState('');
  const navigate = useNavigate();

  const handleAnalyze = (e) => {
    e.preventDefault();
    if (username.trim()) navigate(`/loading?username=${username.trim()}`);
  };

  const features = [
    { icon: <BarChart3 size={20} />, title: '5-Category Scoring', desc: 'AI-powered profile analysis across skills, projects, READMEs, activity, and completeness' },
    { icon: <Briefcase size={20} />, title: 'Job Matching', desc: 'Scan 1300+ internships from SimplifyJobs and match against your profile' },
    { icon: <FileText size={20} />, title: 'Tri-Source Analysis', desc: 'Cross-reference your GitHub, resume, and target JD to find gaps' },
    { icon: <Target size={20} />, title: 'Interview Prep', desc: 'Tailored technical, behavioral, and coding questions for your gaps' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-accent font-bold text-lg">
          <GitBranch size={24} /> GitPulse
        </div>
        <div className="flex gap-4 text-sm text-text-muted">
          <a href="/jobs" className="hover:text-text-primary">Jobs</a>
          <a href="/benchmarks" className="hover:text-text-primary">Benchmarks</a>
          <a href="/history" className="hover:text-text-primary">History</a>
        </div>
      </nav>

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <h1 className="text-4xl md:text-5xl font-bold text-text-primary text-center mb-4">
          Your GitHub Profile,<br /><span className="text-accent">Scored & Optimized</span>
        </h1>
        <p className="text-text-secondary text-center max-w-lg mb-8">
          Autonomous career agent that scores your GitHub profile against job descriptions,
          scans live internships, and opens real PRs to improve your profile.
        </p>

        <form onSubmit={handleAnalyze} className="flex w-full max-w-md gap-2">
          <div className="flex-1 relative">
            <GitBranch size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text" value={username} onChange={(e) => setUsername(e.target.value)}
              placeholder="GitHub username"
              className="w-full pl-9 pr-4 py-2.5 rounded-lg bg-bg-secondary border border-border focus:border-accent outline-none text-text-primary placeholder-text-muted"
            />
          </div>
          <button type="submit" className="px-5 py-2.5 rounded-lg bg-accent hover:bg-accent-dark text-white font-medium flex items-center gap-1">
            <Search size={16} /> Analyze
          </button>
        </form>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-16 w-full max-w-4xl">
          {features.map((f, i) => (
            <div key={i} className="p-4 rounded-lg bg-bg-secondary border border-border hover:border-accent/30 transition-colors">
              <div className="text-accent mb-2">{f.icon}</div>
              <h3 className="text-sm font-medium text-text-primary mb-1">{f.title}</h3>
              <p className="text-xs text-text-muted">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
