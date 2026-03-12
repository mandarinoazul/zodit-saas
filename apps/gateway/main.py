from fastapi import FastAPI, Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from pydantic import BaseModel

app = FastAPI(title="Zodit Gold Cloud Gateway")

# CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to mandev.site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration from Environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
LOCAL_AGENT_URL = os.getenv("LOCAL_AGENT_URL", "https://agent.mandev.site")
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET")

auth_scheme = HTTPBearer()

class CommandRequest(BaseModel):
    command: str
    params: dict = {}

async def get_subscription_tier(user_id: str) -> str:
    """Check subscription tier in Supabase (synced from Polar.sh)"""
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=subscription_tier"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data[0].get("subscription_tier", "free") if data else "free"
        except Exception as e:
            print(f"Error checking subscription: {e}")
        return "free"

async def validate_pro_user(token: HTTPAuthorizationCredentials = Security(auth_scheme)):
    """Validate that the user is logged in and has an active subscription."""
    # Logic to decode Better-Auth JWT/Session would go here
    # For now, we assume the token is validated by a higher-level middleware or proxy
    user_id = "mock_user_from_token" 
    
    tier = await get_subscription_tier(user_id)
    if tier not in ["pro", "enterprise"]:
        raise HTTPException(status_code=403, detail="Active Pro subscription required.")
    
    return {"user_id": user_id, "tier": tier}

@app.get("/health")
async def health():
    return {"status": "online", "service": "gateway"}

@app.post("/agent/execute")
async def forward_to_agent(request: CommandRequest, user: dict = Depends(validate_pro_user)):
    """Forward command to the Local Agent via Cloudflare Tunnel."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LOCAL_AGENT_URL}/api/chat", # Or a specific execute endpoint
                json={"message": request.command, "sender": user["user_id"]},
                headers={"X-API-Key": GATEWAY_SECRET}
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Local Agent unreachable: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
