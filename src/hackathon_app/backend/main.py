import uvicorn
from hackathon_app.backend.app import create_app
from hackathon_app.backend.database import init_db

app = create_app()

# データベース起動用
@app.on_event("startup")
def on_startup():
    init_db()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)




