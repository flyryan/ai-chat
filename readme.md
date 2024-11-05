# AI Chat Assistant

A configurable web application that provides a modern chat interface for any OpenAI-compatible API endpoint. This project includes both a frontend and backend, allowing you to easily deploy your own AI chat interface that works with OpenAI, Azure OpenAI Services, or other compatible endpoints.

## Key Features

- **OpenAI API Compatibility**: Configure any OpenAI-compatible API endpoint through environment variables
- **Modern Chat Interface**: Clean, responsive UI with support for real-time streaming responses
- **Flexible Communication**: Supports both WebSocket and HTTP fallback for chat interactions
- **Markdown Support**: Full Markdown rendering with syntax highlighting for code blocks
- **Azure-Ready**: Includes deployment workflows for Azure, but can be deployed anywhere
- **Configurable Settings**: Easy customization of:
  - API endpoints and credentials
  - Model parameters (temperature, tokens, etc.)
  - UI elements and behavior
  - CORS and security settings

## Installation Guides

### Local Deployment

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo.git
   ```

2. **Run Setup Script**:
   ```bash
   bash setup.sh
   ```
   This script initializes environment files and sets up the virtual environment.

3. **Configure Environment Variables**:

   Backend ([backend/.env](backend/.env)):
   ```
   OPENAI_API_BASE=your-endpoint
   OPENAI_API_KEY=your-key
   OPENAI_DEPLOYMENT_NAME=your-model
   ```

   Frontend ([frontend/.env.development](frontend/.env.development)):
   ```
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_WS_URL=ws://localhost:8000/ws
   ```

4. **Start Backend Server**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn main:app --reload
   ```

5. **Start Frontend Development Server**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

### Azure Deployment

Deployment workflows are provided for Azure:
- Backend: [`.github/workflows/backend-deploy.yml`](.github/workflows/backend-deploy.yml)
- Frontend: [`.github/workflows/frontend-deploy.yml`](.github/workflows/frontend-deploy.yml)

Configure deployment by setting the appropriate secrets in your GitHub repository.

## Development Status

This application is in active development and should be considered unstable. Features and configurations are subject to change without notice. While functional, it may require additional security hardening before production use.