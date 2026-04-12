import { ExternalLink, MapPin } from 'lucide-react';

export default function JobRankTable({ jobs }) {
  if (!jobs || jobs.length === 0) return <p className="text-text-muted text-sm">No jobs found.</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-text-muted border-b border-border">
            <th className="pb-2 pr-4">Company</th>
            <th className="pb-2 pr-4">Role</th>
            <th className="pb-2 pr-4">Location</th>
            <th className="pb-2 pr-4">Posted</th>
            <th className="pb-2">Link</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job, i) => (
            <tr key={i} className="border-b border-border/50 hover:bg-bg-tertiary/50">
              <td className="py-2.5 pr-4 text-text-primary font-medium">{job.company}</td>
              <td className="py-2.5 pr-4 text-text-secondary">{job.role}</td>
              <td className="py-2.5 pr-4 text-text-muted text-xs flex items-center gap-1">
                <MapPin size={10} /> {job.location?.substring(0, 30) || 'N/A'}
              </td>
              <td className="py-2.5 pr-4 text-text-muted text-xs">{job.posted_date || '-'}</td>
              <td className="py-2.5">
                {job.link ? (
                  <a href={job.link} target="_blank" rel="noopener noreferrer" className="text-accent hover:text-accent-light">
                    <ExternalLink size={14} />
                  </a>
                ) : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
