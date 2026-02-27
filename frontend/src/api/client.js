import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// ── Hospital ────────────────────────────
export const getHospital = () => client.get('/hospital');
export const createHospital = (data) => client.post('/hospital', data);
export const updateHospital = (data) => client.put('/hospital', data);

// ── Reviews ─────────────────────────────
export const getReviews = (params) => client.get('/reviews', { params });
export const getReview = (id) => client.get(`/reviews/${id}`);
export const getReviewStats = () => client.get('/reviews/stats');
export const syncReviews = () => client.post('/reviews/sync');

// ── Comments ────────────────────────────
export const generateComments = (reviewId) =>
  client.post(`/reviews/${reviewId}/generate-comments`);
export const getComments = (reviewId) =>
  client.get(`/reviews/${reviewId}/comments`);
export const postComment = (reviewId, commentId) =>
  client.post(`/reviews/${reviewId}/post-comment`, { comment_id: commentId });

// ── Alerts ──────────────────────────────
export const getAlerts = () => client.get('/alerts');
export const markAlertRead = (id) => client.patch(`/alerts/${id}/read`);
export const getUnreadCount = () => client.get('/alerts/unread-count');

// ── Automation ──────────────────────────
export const getAutomationRules = () => client.get('/automation/rules');
export const updateAutomationRules = (data) => client.put('/automation/rules', data);
export const getAutomationLogs = () => client.get('/automation/logs');

export default client;
