import flask
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>ZODIT Dashboard (Stub)</h1><p>El dashboard real está en el frontend de Vercel.</p>"

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT_DASHBOARD", 5001))
    print(f"✅ Dashboard Stub running on port {port}")
    app.run(port=port)
