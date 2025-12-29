/**
 * VELAS Trading System - API Client
 * Axios configuration и base client
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';

// Base URL из переменных окружения или localhost по умолчанию
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Axios instance с базовой конфигурацией
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 секунд
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - добавляем timestamp к каждому запросу
 */
apiClient.interceptors.request.use(
  (config) => {
    // Можно добавить auth token если нужно
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - обработка ошибок
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Сервер ответил с ошибкой
      console.error('API Error:', error.response.status, error.response.data);
      
      // Можно добавить глобальную обработку специфичных ошибок
      if (error.response.status === 401) {
        // Unauthorized - можно редиректить на логин
        console.error('Unauthorized');
      } else if (error.response.status === 500) {
        console.error('Server error');
      }
    } else if (error.request) {
      // Запрос был отправлен, но ответа нет
      console.error('No response from server:', error.request);
    } else {
      // Ошибка при настройке запроса
      console.error('Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Helper для GET запросов
 */
export const get = async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.get<T>(url, config);
  return response.data;
};

/**
 * Helper для POST запросов
 */
export const post = async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
};

/**
 * Helper для PUT запросов
 */
export const put = async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
};

/**
 * Helper для DELETE запросов
 */
export const del = async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
};

/**
 * Helper для формирования query параметров
 */
export const buildQueryString = (params: Record<string, any>): string => {
  const filtered = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
  
  return filtered ? `?${filtered}` : '';
};

/**
 * Helper для проверки доступности API
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await get('/health');
    return response.status === 'healthy';
  } catch {
    return false;
  }
};

export default apiClient;
