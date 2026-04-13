const FIELD_LABELS = {
  // README Quality fields
  has_readme: "Has a README",
  sufficient_length: "Sufficient detail",
  has_headings: "Section headings",
  has_code_blocks: "Code examples",
  has_install_instructions: "Install instructions",
  has_badges_or_images: "Badges or images",
  has_usage_examples: "Usage examples",
  has_screenshots: "Screenshots",
  has_tech_stack: "Tech stack listed",
  has_architecture: "Architecture notes",

  // Profile Completeness fields
  has_avatar: "Profile photo",
  has_name: "Full name",
  has_bio: "Bio",
  has_location: "Location",
  has_company_or_blog: "Company or website",
  has_pinned_repos: "Pinned repositories",
  has_email: "Public email",
};

function humanize(key) {
  if (FIELD_LABELS[key]) return FIELD_LABELS[key];
  return key
    .replace(/^has_/, '')
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

function friendlyReasoning(key, reasoning) {
  if (!reasoning) return null;

  // Activity Level: replace log notation with plain language
  if (key === 'activity_level') {
    const countMatch = reasoning.match(/^(\d+)\s+commits?\s+in\s+/i);
    if (countMatch) {
      const count = parseInt(countMatch[1]);
      if (count === 0) return "No commits in the last 90 days.";
      if (count < 5) return `${count} commits in the last 90 days. Room to grow.`;
      if (count < 30) return `${count} commits in the last 90 days. Moderate activity.`;
      if (count < 100) return `${count} commits in the last 90 days. Good consistent activity.`;
      return `${count} commits in the last 90 days. Strong consistent activity.`;
    }
    // Fallback: strip log notation
    return reasoning.replace(/\s*→\s*log.*$/i, '').replace(/\s*→\s*log₂.*$/i, '');
  }

  // README Quality & Profile Completeness: humanize field names in Passed/Filled/Missing
  let result = reasoning;
  // Replace "Passed: has_readme, has_headings, ..." with human labels
  result = result.replace(/(?:Passed|Filled|Missing):\s*([^.]+)/g, (match, fieldList) => {
    const prefix = match.split(':')[0] + ': ';
    const fields = fieldList.split(',').map((f) => humanize(f.trim()));
    return prefix + fields.join(', ');
  });
  return result;
}

const CATEGORY_LABELS = {
  jd_match: {
    skills_match: "Skills Match",
    project_relevance: "Project Relevance",
    readme_quality: "README Quality",
    activity_level: "Activity Level",
    profile_completeness: "Profile Completeness",
  },
  profile_audit: {
    skills_match: "Skills Profile",
    project_relevance: "Project Quality",
    readme_quality: "README Quality",
    activity_level: "Activity Level",
    profile_completeness: "Profile Completeness",
  },
};

export default function ScoreBreakdown({ breakdown, username, mode }) {
  if (!breakdown) return null;
  const categories = Object.entries(breakdown);
  const labels = CATEGORY_LABELS[mode] || CATEGORY_LABELS.profile_audit;

  return (
    <div className="space-y-3">
      {categories.map(([key, data]) => {
        const score = data.score ?? data;
        const max = data.max ?? 100;
        const pct = Math.round((score / max) * 100);
        const label = labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
        const color = pct >= 75 ? 'bg-success' : pct >= 50 ? 'bg-warning' : 'bg-danger';
        const reasoning = friendlyReasoning(key, data.reasoning);

        // Detect if reasoning contains "Missing:" for profile completeness hint
        const hasMissing = key === 'profile_completeness' && reasoning && reasoning.includes('Missing:');

        return (
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text-secondary">{label}</span>
              <span className="text-text-primary font-medium">{score}/{max}</span>
            </div>
            <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${color} transition-all duration-700`} style={{ width: `${pct}%` }} />
            </div>
            {reasoning && (
              <p className="text-xs text-text-muted mt-1">{reasoning}</p>
            )}
            {hasMissing && username && (
              <p className="text-xs text-accent-light mt-1">
                Tip: Update these at github.com/{username} &rarr; Edit profile
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
