const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export const BASE_URL = API_BASE_URL;

export const api = {
  /**
   * 1. Get Opik Dashboard Stats (A/B Tests & Trends)
   */
  getOpikStats: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/opik/dashboard-stats`);
      if (!response.ok) {
        // It is okay to fail here (e.g. if Opik is down), just return null so UI handles it gracefully
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      return null; 
    }
  },

  /**
   * 2. Start a new analysis job
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
   * 3. Check the status of a running job
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
   * 4. Get the final result of a completed job
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
   * 5. Get user history from DB (Persistent History)
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
  },

/**
 * 6. Submit Human Feedback (Thumbs Up/Down)
 */
submitFeedback: async (jobId, score, comment = null) => {
  console.log("Sending Feedback Payload:", { job_id: jobId, score, comment }); // DEBUG
  try {
    const response = await fetch(`${API_BASE_URL}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: jobId,   
        score: score,      
        comment: comment   
      })
    });
    
    if (!response.ok) {
    const errorData = await response.json();
    // Stringify the error detail so it's readable in the console
    throw new Error(JSON.stringify(errorData.detail) || 'Failed to submit feedback');
}
    
    return await response.json();
  } catch (error) {
    console.error('Feedback API Error:', error);
    throw error;
  }
}
};