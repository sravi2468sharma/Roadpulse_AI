const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let message = `RoadPulse API error: ${response.status}`;
    try {
      const payload = await response.json();
      const detail = payload.detail;
      message = typeof detail === 'string' ? detail : detail?.message || message;
      if (detail?.required_files?.length) message += ` Required: ${detail.required_files.join(', ')}`;
    } catch {
      // Keep the HTTP status when the server response is not JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export const getDashboardSummary = () => request('/api/dashboard/summary');
export const getHealth = () => request('/health');
export const getLocations = () => request('/api/locations');
export const getRiskMap = () => request('/api/risk-map');
export const getLocation = (id) => request(`/api/locations/${id}`);
export const getCauses = (id) => request(`/api/locations/${id}/causes`);
export const getVulnerability = (id) => request(`/api/locations/${id}/vulnerability`);
export const getTemporal = (id) => request(`/api/locations/${id}/temporal`);
export const getPrediction = (id) => request(`/api/locations/${id}/prediction`);
export const getInterventions = (id) => request(`/api/locations/${id}/interventions`);
export const getActionPlan = () => request('/api/action-plan');
export const getModelMetrics = () => request('/api/model/metrics');
export const getNationalCauses = () => request('/api/national/causes');
export const getNationalVulnerability = () => request('/api/national/vulnerability');
export const simulateInterventions = (location_id, intervention_ids) => request('/api/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location_id, intervention_ids }) });
export const uploadData = (file) => { const body = new FormData(); body.append('file', file); return request('/api/data/upload', { method: 'POST', body }); };