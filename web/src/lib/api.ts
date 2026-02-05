/**
 * FastAPI Backend API Client
 * Handles all API calls to the FastAPI backend
 */

import { auth } from './firebase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

/**
 * Get Firebase ID token for authentication
 * Automatically refreshes expired tokens
 */
async function getAuthToken(forceRefresh: boolean = false): Promise<string | null> {
  try {
    const user = auth.currentUser;
    if (!user) {
      console.warn('[API] No authenticated user found');
      return null;
    }
    // getIdToken() automatically refreshes expired tokens
    // forceRefresh=true forces a refresh even if token is still valid
    const token = await user.getIdToken(forceRefresh);
    return token;
  } catch (error) {
    console.error('[API] Error getting auth token:', error);
    return null;
  }
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();
  
  if (!token) {
    const error = new Error('Not authenticated. Please log in to continue.');
    console.error('[API] Authentication failed:', {
      endpoint,
      hasUser: !!auth.currentUser,
    });
    throw error;
  }

  const url = `${API_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `API request failed: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorJson.message || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    
    // Log detailed error for debugging
    console.error('API Error:', {
      url,
      status: response.status,
      statusText: response.statusText,
      error: errorMessage,
      body: errorText,
    });
    
    throw new Error(errorMessage);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

/**
 * Session API
 */
export const sessionsApi = {
  /**
   * Get list of sessions
   */
  async list(params?: {
    skip?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    topic?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.topic) queryParams.append('topic', params.topic);

    const queryString = queryParams.toString();
    return apiRequest<{
      sessions: any[];
      total: number;
      skip: number;
      limit: number;
    }>(`/sessions${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get a single session
   */
  async get(sessionId: string) {
    return apiRequest<any>(`/sessions/${sessionId}`);
  },

  /**
   * Get session statistics
   */
  async getStats(days: number = 7) {
    return apiRequest<{
      total_sessions: number;
      total_duration: number;
      total_hours: number;
      avg_focus_score: number;
      avg_productivity_score: number;
      period_days: number;
    }>(`/sessions/stats/summary?days=${days}`);
  },
};

/**
 * User API
 */
export const usersApi = {
  /**
   * Get current user info
   */
  async getCurrent() {
    return apiRequest<any>('/auth/me');
  },

  /**
   * Get user by ID
   */
  async get(userId: string) {
    return apiRequest<any>(`/users/${userId}`);
  },

  /**
   * Get user stats
   */
  async getStats(userId: string) {
    return apiRequest<{
      user_id: string;
      total_sessions: number;
      total_hours: number;
      average_focus_score: number;
      average_productivity_score: number;
      topic_distribution: Record<string, number>;
      study_heatmap: Record<string, number>;
      weekly_trend: number[];
    }>(`/users/${userId}/stats`);
  },
};

/**
 * Todos API
 */
export const todosApi = {
  /**
   * Get list of todos
   */
  async list(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    priority?: string;
    category?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.priority) queryParams.append('priority', params.priority);
    if (params?.category) queryParams.append('category', params.category);

    const queryString = queryParams.toString();
    return apiRequest<{
      todos: any[];
      total: number;
      skip: number;
      limit: number;
    }>(`/todos${queryString ? `?${queryString}` : ''}`);
  },

  /**
   * Get a single todo
   */
  async get(todoId: string) {
    return apiRequest<any>(`/todos/${todoId}`);
  },

  /**
   * Create a new todo
   */
  async create(data: {
    title: string;
    description?: string;
    estimated_minutes?: number;
    due_date?: string;
    scheduled_date?: string;
    category?: string;
    priority?: string;
  }) {
    return apiRequest<any>('/todos/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a todo
   */
  async update(todoId: string, data: {
    title?: string;
    description?: string;
    estimated_minutes?: number;
    due_date?: string;
    scheduled_date?: string;
    category?: string;
    priority?: string;
    status?: string;
  }) {
    return apiRequest<any>(`/todos/${todoId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a todo
   */
  async delete(todoId: string) {
    return apiRequest<void>(`/todos/${todoId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Complete a todo
   */
  async complete(todoId: string, actualMinutes?: number) {
    const queryParams = new URLSearchParams();
    if (actualMinutes !== undefined) {
      queryParams.append('actual_minutes', actualMinutes.toString());
    }
    const queryString = queryParams.toString();
    return apiRequest<any>(`/todos/${todoId}/complete${queryString ? `?${queryString}` : ''}`, {
      method: 'POST',
    });
  },
};

/**
 * Health check
 */
export async function healthCheck() {
  try {
    const response = await fetch(`${API_URL}/health`);
    return response.json();
  } catch (error) {
    console.error('Health check failed:', error);
    return null;
  }
}
