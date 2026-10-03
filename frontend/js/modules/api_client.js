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
};
