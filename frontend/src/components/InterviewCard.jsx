import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function InterviewCard({ question, type = 'technical' }) {
  const [open, setOpen] = useState(false);
  const colors = {
    technical: 'border-accent/30 hover:border-accent',
    behavioral: 'border-warning/30 hover:border-warning',
    coding: 'border-success/30 hover:border-success',
    gap: 'border-danger/30 hover:border-danger',
  };

  return (
    <div className={`rounded-lg bg-bg-tertiary border ${colors[type] || colors.technical} transition-colors`}>
      <button onClick={() => setOpen(!open)} className="w-full p-4 text-left flex items-start justify-between gap-2">
        <div>
          <p className="text-sm text-text-primary">{question.question || question.problem}</p>
          {question.skill_tested && (
            <span className="text-xs text-accent-light mt-1 inline-block">{question.skill_tested}</span>
          )}
          {question.difficulty && (
            <span className={`text-xs mt-1 inline-block ml-2 px-1.5 py-0.5 rounded ${
              question.difficulty === 'easy' ? 'bg-success/10 text-success' :
              question.difficulty === 'hard' ? 'bg-danger/10 text-danger' : 'bg-warning/10 text-warning'
            }`}>{question.difficulty}</span>
          )}
        </div>
        {open ? <ChevronUp size={16} className="text-text-muted shrink-0" /> : <ChevronDown size={16} className="text-text-muted shrink-0" />}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-2 text-sm border-t border-border/50 pt-3">
          {question.why_asked && <p className="text-text-muted"><span className="text-text-secondary font-medium">Why asked:</span> {question.why_asked}</p>}
          {question.suggested_answer_framework && <p className="text-text-muted"><span className="text-text-secondary font-medium">Framework:</span> {question.suggested_answer_framework}</p>}
          {question.hint && <p className="text-text-muted"><span className="text-text-secondary font-medium">Hint:</span> {question.hint}</p>}
          {question.topics && <div className="flex gap-1 flex-wrap">{question.topics.map((t) => <span key={t} className="text-xs px-1.5 py-0.5 rounded bg-accent/10 text-accent-light">{t}</span>)}</div>}
          {question.gap && <p className="text-text-muted"><span className="text-danger font-medium">Gap:</span> {question.gap}</p>}
          {question.how_to_prepare && <p className="text-text-muted"><span className="text-text-secondary font-medium">Prepare:</span> {question.how_to_prepare}</p>}
          {question.backup_answer && <p className="text-text-muted"><span className="text-text-secondary font-medium">Backup:</span> {question.backup_answer}</p>}
        </div>
      )}
    </div>
  );
}
