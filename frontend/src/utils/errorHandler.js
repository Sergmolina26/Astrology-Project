// Utility function to extract error messages from API responses
export const extractErrorMessage = (error, defaultMessage = 'An error occurred') => {
  if (!error) return defaultMessage;
  
  // If error is already a string
  if (typeof error === 'string') return error;
  
  // Check response data
  if (error.response?.data) {
    const data = error.response.data;
    
    // If data is a string
    if (typeof data === 'string') return data;
    
    // Check detail field (common in FastAPI)
    if (data.detail) {
      if (typeof data.detail === 'string') return data.detail;
      if (Array.isArray(data.detail)) {
        // Pydantic validation errors
        const firstError = data.detail[0];
        if (firstError?.msg) return firstError.msg;
        if (typeof firstError === 'string') return firstError;
      }
    }
    
    // Check message field
    if (data.message && typeof data.message === 'string') {
      return data.message;
    }
    
    // Check error field
    if (data.error && typeof data.error === 'string') {
      return data.error;
    }
  }
  
  // Check error message
  if (error.message && typeof error.message === 'string') {
    return error.message;
  }
  
  return defaultMessage;
};