import { Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Loading from './pages/Loading';
import Results from './pages/Results';
import JobBoard from './pages/JobBoard';
import Progress from './pages/Progress';
import TriMatch from './pages/TriMatch';
import Benchmarks from './pages/Benchmarks';
import InterviewPrep from './pages/InterviewPrep';
import History from './pages/History';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/loading" element={<Loading />} />
      <Route path="/results" element={<Results />} />
      <Route path="/jobs" element={<JobBoard />} />
      <Route path="/progress" element={<Progress />} />
      <Route path="/tri-match" element={<TriMatch />} />
      <Route path="/benchmarks" element={<Benchmarks />} />
      <Route path="/interview-prep" element={<InterviewPrep />} />
      <Route path="/history" element={<History />} />
    </Routes>
  );
}
