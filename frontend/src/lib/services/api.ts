const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

async function request<T>(path: string, options: RequestInit = {}) {
	const headers = new Headers(options.headers);
	if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

	const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || `Request failed with status ${response.status}`);
	}

	if (response.status === 204) return undefined as T;
	return (await response.json()) as T;
}

export const api = {
	request,
	health: () => request<{ status: string }>('/system/health'),
	monitoring: {
		getSessions: (params?: Record<string, string>) => request('/monitoring/sessions' + toQuery(params)),
		startSession: (data: unknown) => json('/monitoring/sessions/start', 'POST', data),
		stopSession: (id: string) => json(`/monitoring/sessions/${id}/stop`, 'PUT'),
		getSession: (id: string) => request(`/monitoring/sessions/${id}`),
		startSimulator: (clientId: string) => json('/monitoring/simulate/start', 'POST', { client_id: clientId }),
		stopSimulator: (clientId: string) => json(`/monitoring/simulate/stop/${clientId}`, 'POST'),
		getLiveData: (clientId: string) => request(`/monitoring/live/${clientId}`)
	},
	fl: {
		getStatus: () => request('/fl/status'),
		getRounds: (params?: Record<string, string>) => request('/fl/rounds' + toQuery(params)),
		getRound: (id: string) => request(`/fl/rounds/${id}`),
		startTraining: (data: unknown) => json('/fl/training/start', 'POST', data),
		stopTraining: () => json('/fl/training/stop', 'POST'),
		getClients: () => request('/fl/clients'),
		getClient: (id: string) => request(`/fl/clients/${id}`),
		getAggregation: (roundId: string) => request(`/fl/aggregation/${roundId}`),
		getGlobalModel: () => request('/fl/global-model'),
		getModelHistory: () => request('/fl/global-model/history'),
		getPersonalModels: () => request('/fl/personal-models'),
		getPersonalModel: (userId: string) => request(`/fl/personal-models/${userId}`)
	},
	experiments: {
		getExperiments: () => request('/experiments'),
		createExperiment: (data: unknown) => json('/experiments', 'POST', data),
		getExperiment: (id: string) => request(`/experiments/${id}`),
		runExperiment: (id: string) => json(`/experiments/${id}/run`, 'POST'),
		getResults: (id: string) => request(`/experiments/${id}/results`),
		runRobustness: (data: unknown) => json('/experiments/robustness/run', 'POST', data),
		runAblation: (data: unknown) => json('/experiments/ablation/run', 'POST', data)
	},
	devices: {
		getDevices: () => request('/devices'),
		createDevice: (data: unknown) => json('/devices', 'POST', data),
		getDevice: (id: string) => request(`/devices/${id}`),
		updateDevice: (id: string, data: unknown) => json(`/devices/${id}`, 'PUT', data),
		deleteDevice: (id: string) => request(`/devices/${id}`, { method: 'DELETE' }),
		connectDevice: (id: string) => json(`/devices/${id}/connect`, 'POST'),
		disconnectDevice: (id: string) => json(`/devices/${id}/disconnect`, 'POST')
	},
	alerts: {
		getRules: () => request('/alerts/rules'),
		createRule: (data: unknown) => json('/alerts/rules', 'POST', data),
		updateRule: (id: string, data: unknown) => json(`/alerts/rules/${id}`, 'PUT', data),
		deleteRule: (id: string) => request(`/alerts/rules/${id}`, { method: 'DELETE' }),
		getNotifications: (params?: Record<string, string>) => request('/alerts/notifications' + toQuery(params)),
		markRead: (id: string) => json(`/alerts/notifications/${id}/read`, 'PUT'),
		markAllRead: () => json('/alerts/notifications/read-all', 'PUT'),
		dismiss: (id: string) => request(`/alerts/notifications/${id}`, { method: 'DELETE' })
	},
	reports: {
		generate: (data: unknown) => json('/reports/generate', 'POST', data),
		getReports: () => request('/reports'),
		download: (id: string) => fetch(`${API_BASE}/reports/${id}/download`)
	},
	system: {
		getHealth: () => request('/system/health'),
		getLogs: (params?: Record<string, string>) => request('/system/logs' + toQuery(params)),
		getStats: () => request('/system/stats'),
		getSettings: () => request('/system/settings'),
		updateSettings: (data: unknown) => json('/system/settings', 'PUT', data)
	}
};

function toQuery(params?: Record<string, string>) {
	if (!params) return '';
	const query = new URLSearchParams(params).toString();
	return query ? `?${query}` : '';
}

function json<T>(path: string, method: string, body?: unknown) {
	return request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
}

export { API_BASE };