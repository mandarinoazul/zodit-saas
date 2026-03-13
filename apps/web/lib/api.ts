import { supabase } from "./supabase";

export const fetchWithKey = async (endpoint: string, options: RequestInit = {}) => {
  // Check for custom gateway URL in localStorage (Client side only)
  let gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8001';
  
  if (typeof window !== 'undefined') {
    const customUrl = localStorage.getItem('zodit_custom_gateway');
    if (customUrl && customUrl.trim() !== '') {
      gatewayUrl = customUrl;
    }
  }

  const apiKey = process.env.NEXT_PUBLIC_GATEWAY_SECRET || '';
  
  const { data: { session } } = await supabase.auth.getSession();
  const userId = session?.user?.id || 'anonymous';

  const defaultHeaders = {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey,
    'X-User-ID': userId,
  };

  const response = await fetch(`${gatewayUrl}${endpoint}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error ${response.status}: ${errorBody}`);
  }

  return response.json();
};
