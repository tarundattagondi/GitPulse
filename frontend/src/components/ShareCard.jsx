import { Share2, Copy, Check } from 'lucide-react';
import { useState } from 'react';

export default function ShareCard({ username, score, matchPct }) {
  const [copied, setCopied] = useState(false);

  const text = `GitPulse Profile Score: ${score}/100${matchPct ? ` | Job Match: ${matchPct}%` : ''}\nAnalyzed with GitPulse - github.com/tarundattagondi/GitPulse`;

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-4 rounded-lg bg-bg-tertiary border border-border">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-text-primary flex items-center gap-1">
          <Share2 size={14} /> Share Results
        </h4>
        <button onClick={handleCopy} className="text-xs text-accent hover:text-accent-light flex items-center gap-1">
          {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
        </button>
      </div>
      <pre className="text-xs text-text-muted whitespace-pre-wrap">{text}</pre>
    </div>
  );
}
