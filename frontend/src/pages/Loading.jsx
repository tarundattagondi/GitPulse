import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { analyzeProfile } from '../services/api';

const STEPS = ['Fetching GitHub profile...', 'Analyzing repositories...', 'Scoring with AI...', 'Computing results...'];

export default function Loading() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const username = params.get('username');
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!username) { navigate('/'); return; }

    const timer = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 2000);

    analyzeProfile(username)
      .then((res) => {
        clearInterval(timer);
        navigate('/results', { state: { data: res.data, username } });
      })
      .catch((err) => {
        clearInterval(timer);
        setError(err.message);
      });

    return () => clearInterval(timer);
  }, [username, navigate]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      {error ? (
        <div className="text-center">
          <p className="text-danger text-lg mb-2">Analysis failed</p>
          <p className="text-text-muted text-sm mb-4">{error}</p>
          <button onClick={() => navigate('/')} className="px-4 py-2 rounded-lg bg-accent text-white text-sm">Go back</button>
        </div>
      ) : (
        <div className="text-center">
          <Loader2 size={40} className="text-accent animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">Analyzing {username}</h2>
          <div className="space-y-2 mt-4">
            {STEPS.map((s, i) => (
              <p key={i} className={`text-sm transition-colors ${i <= step ? 'text-text-primary' : 'text-text-muted'}`}>
                {i < step ? '✓' : i === step ? '→' : '○'} {s}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
