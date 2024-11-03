# backend/main.py

# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGINS", "https://ludus-chat-frontend.azurewebsites.net")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
