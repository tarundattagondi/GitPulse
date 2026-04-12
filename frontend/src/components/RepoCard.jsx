import { Star, GitFork, Code } from 'lucide-react';

export default function RepoCard({ repo }) {
  return (
    <a
      href={repo.html_url} target="_blank" rel="noopener noreferrer"
      className="block p-4 rounded-lg bg-bg-tertiary border border-border hover:border-accent/50 transition-colors"
    >
      <div className="flex items-start justify-between">
        <h4 className="font-medium text-text-primary">{repo.name}</h4>
        <div className="flex items-center gap-3 text-xs text-text-muted">
          <span className="flex items-center gap-1"><Star size={12} /> {repo.stars}</span>
          <span className="flex items-center gap-1"><GitFork size={12} /> {repo.forks}</span>
        </div>
      </div>
      <p className="text-sm text-text-secondary mt-1 line-clamp-2">{repo.description || 'No description'}</p>
      {repo.language && (
        <div className="flex items-center gap-1 mt-2 text-xs text-accent-light">
          <Code size={12} /> {repo.language}
        </div>
      )}
    </a>
  );
}
