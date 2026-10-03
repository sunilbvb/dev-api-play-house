/**
 * Client for Dev API Play House backend REST API
 */

const BASE_URL = window.location.origin;

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(url, config);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `HTTP error! status: ${response.status}`);
  }

  return data;
}

export const apiClient = {
  // Health
  getHealth: () => request('/api/health'),

  // Environments
  getEnvironments: () => request('/api/environments'),
  createEnvironment: (name, variables) => request('/api/environments', { method: 'POST', body: { name, variables } }),
  updateEnvironment: (id, name, variables) => request(`/api/environments/${id}`, { method: 'PUT', body: { name, variables } }),
  deleteEnvironment: (id) => request(`/api/environments/${id}`, { method: 'DELETE' }),
  setActiveEnvironment: (id) => request('/api/environments/active', { method: 'POST', body: { id } }),

  // Collections
  getCollections: () => request('/api/collections'),
  createCollection: (name, description = '') => request('/api/collections', { method: 'POST', body: { name, description } }),
  deleteCollection: (id) => request(`/api/collections/${id}`, { method: 'DELETE' }),

  // Requests
  getRequests: (collectionId = null) => {
    const q = collectionId ? `?collection_id=${collectionId}` : '';
    return request(`/api/requests${q}`);
  },
  createRequest: (payload) => request('/api/requests', { method: 'POST', body: payload }),
  updateRequest: (id, payload) => request(`/api/requests/${id}`, { method: 'PUT', body: payload }),
  deleteRequest: (id) => request(`/api/requests/${id}`, { method: 'DELETE' }),

  // Execution
  executeRequest: (payload) => request('/api/execute', { method: 'POST', body: payload }),

  // Import / Export
  importApis: (type, content, collectionName) => request('/api/import', {
    method: 'POST',
    body: { type, content, collection_name: collectionName },
  }),
  exportApis: (format, requestsList, collectionName) => request('/api/export', {
    method: 'POST',
    body: { format, requests: requestsList, collection_name: collectionName },
  }),

  // Workflows & DAG
  analyzeWorkflow: (collectionId) => request('/api/workflows/analyze', { method: 'POST', body: { collection_id: collectionId } }),
  runWorkflow: (collectionId, runtimeVars = {}) => request('/api/workflows/run', {
    method: 'POST',
    body: { collection_id: collectionId, runtime_variables: runtimeVars },
  }),

  // Game House Auto-Architect & Vitals
  autoBuildHouse: (payload) => request('/api/house/auto-build', { method: 'POST', body: payload }),
  getHouseVitals: (collectionId) => request(`/api/house/${collectionId}/vitals`),

  // Gamification & Features
  getTrophies: () => request('/api/trophies'),
  getCoopEvents: (sinceId = 0) => request(`/api/coop/events?since_id=${sinceId}`),
  postCoopEvent: (actor, message) => request('/api/coop/events', { method: 'POST', body: { actor, message } }),
  generateSideQuests: (requestId) => request('/api/fuzzer/generate-side-quests', { method: 'POST', body: { request_id: requestId } }),
  getReplayFrames: () => request('/api/replay/frames'),
  exportReplayTape: () => request('/api/replay/export', { method: 'POST' }),

  // Auto-Documentation & Test Advisor
  generateApiDocs: (payload) => request('/api/docs/generate', { method: 'POST', body: payload }),
  analyzeTestWays: (payload) => request('/api/advisor/analyze-test-ways', { method: 'POST', body: payload }),
  runTestWays: (payload) => request('/api/advisor/run-test-ways', { method: 'POST', body: payload }),
};
