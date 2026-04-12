import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { GitBranch, Search, Filter } from 'lucide-react';
import { listJobs } from '../services/api';
import JobRankTable from '../components/JobRankTable';

export default function JobBoard() {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [role, setRole] = useState('software');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);

  const search = () => {
    setLoading(true);
    listJobs(role || undefined, location || undefined)
      .then((res) => { setJobs(res.data.jobs); setTotal(res.data.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { search(); }, []);

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-accent font-bold"><GitBranch size={20} /> GitPulse</Link>
        <span className="text-text-muted text-sm">Job Board</span>
      </nav>
      <div className="max-w-5xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-text-primary mb-6">Summer 2026 Internships</h1>
        <div className="flex gap-2 mb-6">
          <div className="relative flex-1">
            <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Role (e.g. software, data)"
              className="w-full pl-8 pr-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent" />
          </div>
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Location (e.g. NYC, SF)"
              className="w-full pl-8 pr-3 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary text-sm outline-none focus:border-accent" />
          </div>
          <button onClick={search} disabled={loading} className="px-4 py-2 rounded-lg bg-accent hover:bg-accent-dark text-white text-sm disabled:opacity-50">
            {loading ? 'Loading...' : 'Search'}
          </button>
        </div>
        <p className="text-text-muted text-sm mb-4">{total} results</p>
        <JobRankTable jobs={jobs} />
      </div>
    </div>
  );
}
