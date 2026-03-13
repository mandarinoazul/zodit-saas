export async function fetchWithKey(endpoint: string, options: RequestInit = {}) {
    const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "";
    const gatewayKey = process.env.NEXT_PUBLIC_GATEWAY_SECRET || "";
    
    const url = endpoint.startsWith('http') ? endpoint : `${gatewayUrl}${endpoint}`;
    
    const res = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": gatewayKey,
            ...options.headers,
        },
    });
    
    if (!res.ok) {
        throw new Error(`API Error: ${res.status}`);
    }
    
    return res.json();
}
