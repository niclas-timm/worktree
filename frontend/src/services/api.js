import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email, password) => api.post("/auth/login/", { email, password }),

  register: (name, email, password) =>
    api.post("/auth/registration/", { name, email, password1: password }),

  logout: () => api.post("/auth/logout/"),

  getUser: () => api.get("/auth/user/"),

  verifyEmail: (email, code) => api.post("/auth/verify-email/", { email, code }),

  resendVerificationCode: (email) => api.post("/auth/resend-verification/", { email }),
};

export default api;
