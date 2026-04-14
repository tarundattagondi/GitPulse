import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 180000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.message || err.response?.data?.error || err.message;
    return Promise.reject(new Error(message));
  }
);

export const analyzeProfile = (username, roleCategory = 'other') =>
  api.get(`/api/analyze/${username}`, { params: { role_category: roleCategory } });

export const analyzeProfileWithJD = (username, jdText, roleCategory = 'other') =>
  api.post(`/api/analyze/${username}?role_category=${roleCategory}`, { jd_text: jdText });

export const scoreProfile = (username, jobDescription, roleCategory = 'other') =>
  api.get(`/api/score/${username}`, { params: { job_description: jobDescription, role_category: roleCategory } });

export const listJobs = (role, location, excludeClosed = true) =>
  api.get('/api/jobs', { params: { role, location, exclude_closed: excludeClosed } });

export const scanJobs = (username, roleFilters, locationFilters, maxJobs = 30) =>
  api.post('/api/scan-jobs', { username, role_filters: roleFilters, location_filters: locationFilters, max_jobs: maxJobs });

export const scanJobsStatus = (scanId) =>
  api.get(`/api/scan-jobs/status/${scanId}`);

export const previewPR = (username, repoName, token) =>
  api.post('/api/pr/preview', { username, repo_name: repoName, token });

export const openPR = (username, repoName, newReadmeContent, token) =>
  api.post('/api/pr/open', { username, repo_name: repoName, new_readme_content: newReadmeContent, token });

export const getProgress = (username, roleCategory, days = 90) =>
  api.get(`/api/progress/${username}`, { params: { role_category: roleCategory, days } });

export const triMatch = (formData) =>
  api.post('/api/tri-match', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

export const listCompanies = () =>
  api.get('/api/benchmark/companies');

export const getBenchmark = (username, company) =>
  api.get(`/api/benchmark/${username}/${company}`);

export const getInterviewPrep = (username, jdText) =>
  api.post('/api/interview-prep', { username, jd_text: jdText });

export const getLatestAnalysis = (username) =>
  api.get(`/api/analysis/${username}/latest`);

export default api;
