import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import api from '../services/api';

const STEPS = [
  'Fetching GitHub profile...',
  'Analyzing repositories & languages...',
  'Scoring with Claude AI...',
  'Computing category breakdown...',
  'Finalizing results...',
];

export default function Loading() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const username = params.get('username');
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!username) { navigate('/'); return; }

    // Read JD from sessionStorage (set by Landing page)
    const jdText = sessionStorage.getItem('gitpulse_jd') || '';
    const hasJd = jdText.length >= 50;

    console.log('GitPulse: starting analysis', { username, jdLength: jdText.length, mode: hasJd ? 'jd_match' : 'profile_audit' });

    const timers = [
      setTimeout(() => setStep(1), 3000),
      setTimeout(() => setStep(2), 10000),
      setTimeout(() => setStep(3), 25000),
      setTimeout(() => setStep(4), 45000),
    ];

    // Always use POST — sends jd_text (empty string = profile audit, non-empty = JD match)
    api.post(`/api/analyze/${encodeURIComponent(username)}?role_category=other`, { jd_text: jdText })
      .then((res) => {
        timers.forEach(clearTimeout);
        sessionStorage.removeItem('gitpulse_jd');
        navigate('/results', { state: { data: res.data, username } });
      })
      .catch((err) => {
        timers.forEach(clearTimeout);
        console.error('GitPulse: analyze failed', { error: err, response: err.response?.data });
        if (err.code === 'ECONNABORTED' || err.message?.includes('timeout') || err.message?.includes('Network Error')) {
          setError(
            'Analysis is taking longer than expected. The backend may still be working — ' +
            'check the Progress page in a minute.'
          );
        } else {
          setError(err.response?.data?.detail || err.message || 'Network Error');
        }
      });

    return () => timers.forEach(clearTimeout);
  }, [username, navigate]);

  const jdText = typeof window !== 'undefined' ? sessionStorage.getItem('gitpulse_jd') || '' : '';
  const hasJd = jdText.length >= 50;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      {error ? (
        <div className="text-center max-w-md">
          <p className="text-danger text-lg mb-2">Analysis failed</p>
          <p className="text-text-muted text-sm mb-4">{error}</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/')} className="px-4 py-2 rounded-lg bg-accent text-white text-sm">Go back</button>
            <Link to={`/history?username=${username}`} className="px-4 py-2 rounded-lg bg-bg-secondary border border-border text-text-secondary text-sm">Check history</Link>
          </div>
        </div>
      ) : (
        <div className="text-center">
          <Loader2 size={40} className="text-accent animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            {hasJd ? `Matching ${username} against JD` : `Auditing ${username}'s profile`}
          </h2>
          <div className="space-y-2 mt-4">
            {STEPS.map((s, i) => (
              <p key={i} className={`text-sm transition-colors duration-500 ${i <= step ? 'text-text-primary' : 'text-text-muted'}`}>
                {i < step ? '\u2713' : i === step ? '\u2192' : '\u25CB'} {s}
              </p>
            ))}
          </div>
          <p className="text-text-muted text-xs mt-6">
            This usually takes 30-60 seconds.{hasJd ? ' JD matching adds ~20 seconds.' : ''}<br />
            First analysis after a cold start can take up to 2 minutes.
          </p>
        </div>
      )}
    </div>
  );
}
