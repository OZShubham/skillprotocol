const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = {
  /**
   * Start a new analysis job
   */
  analyzeRepo: async (repoUrl, userId = 'demo-user', token = null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_url: repoUrl,
          user_id: userId,
          github_token: token
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed to start');
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  /**
   * Check the status of a running job
   */
  checkStatus: async (jobId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  /**
   * Get the final result of a completed job
   */
  getResult: async (jobId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/result/${jobId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  /**
   * Get user history from DB
   * This is the new function needed for persistent history
   */
  getUserHistory: async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/user/${userId}/history`);
      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      return []; // Return empty array on error so UI doesn't crash
    }
  }
};