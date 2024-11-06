# AI Chat Assistant

A configurable web application that provides a modern chat interface for any OpenAI-compatible API endpoint. This project includes both a frontend and backend, allowing you to easily deploy your own AI chat interface that works with OpenAI, Azure OpenAI Services, or other compatible endpoints.

## Key Features

### OpenAI API Compatibility
Configure any OpenAI-compatible API endpoint through environment variables.

### Modern Chat Interface
Clean, responsive UI with support for real-time streaming responses.

### Flexible Communication
Supports both WebSocket and HTTP fallback for chat interactions.

### Markdown Support
Full Markdown rendering with syntax highlighting for code blocks.

### Azure-Ready
Includes deployment workflows for Azure, but can be deployed anywhere.

### Configurable Settings
Easily customize various aspects of the application, including:

- **API Endpoints and Credentials**: Set up different API endpoints and manage credentials effortlessly.
- **Model Parameters**: Adjust parameters such as temperature, token limits, and more to fine-tune the model's behavior.
- **UI Elements and Behavior**: Personalize the user interface and interaction patterns to suit your needs.
- **CORS and Security Settings**: Configure Cross-Origin Resource Sharing (CORS) and other security settings.

## How It Works

### Languages and Technologies

- **Frontend**: Built with React.
- **Backend**: Developed using FastAPI with Python 3.9+.
- **WebSockets**: Utilized for real-time communication between the frontend and backend.
- **Markdown Rendering**: Supports full Markdown rendering with syntax highlighting for code blocks.

### Architecture

The application follows a client-server architecture:

- **Frontend**: The React-based frontend communicates with the backend via HTTP and WebSocket protocols. It provides a clean and responsive user interface for interacting with the AI model.
- **Backend**: The FastAPI-based backend handles API requests, processes data, and communicates with the OpenAI-compatible endpoints. It also manages WebSocket connections for real-time interactions.

### Cross-Platform Nature

The application is designed to be cross-platform and can be deployed on various environments, including:

- **Local Machines**: Easily set up and run the application on your local development environment.
- **Cloud Platforms**: Deployable on cloud platforms such as Azure, AWS, and Google Cloud.
- **Containers**: Can be containerized using Docker for consistent deployment across different environments.

## Installation Guides

### Local Deployment

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/flyryan/ai-chat.git
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
   # The deployment name will likely be gpt-4o (or o1 or whatever is new) but could be different if you deployed your own model on Azure or are pointing to an external model.
   ```

   Frontend ([frontend/.env.development](frontend/.env.development)):
   ```
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_WS_URL=ws://localhost:8000/ws
   ```

4. **Start Backend Server**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

5. **Start Frontend Development Server**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

### Azure Deployment

This section provides a step-by-step guide to deploying the application to Azure, including setting the necessary environment variables.

#### Prerequisites

- **Azure Account**: An active Azure subscription.
- **Azure Resources**:
  - **Azure App Service** for the backend.
  - **Azure Static Web Apps** for the frontend.
  - **Azure OpenAI Service** with a deployed model.
  - **Azure Cognitive Search** (if using vector search features).
- **Azure CLI**: Installed and logged in to your Azure account.
- **GitHub Repository**: Access to set repository secrets and modify workflows.

#### Backend Deployment (Azure App Service)

1. **Create an Azure App Service**:

   - Navigate to the Azure Portal and create a new **App Service**.
   - Choose **Runtime stack**: Python 3.9 or compatible.
   - Note down the **App Service name** and **Resource Group**.

2. **Configure Application Settings**:

   - In the App Service, go to **Configuration** > **Application settings**.
   - Add the following environment variables:

     | Key                          | Value                                  | Description                                       |
     |------------------------------|----------------------------------------|---------------------------------------------------|
     | `APP_NAME`                   | Your application name                  | For display purposes                              |
     | `ENVIRONMENT`                | `production`                           | Sets the environment mode                         |
     | `OPENAI_API_KEY`             | *Your OpenAI API key*                  | From Azure OpenAI Service                         |
     | `OPENAI_API_BASE`            | *Your OpenAI API endpoint*             | e.g., `https://your-resource.openai.azure.com/`   |
     | `OPENAI_API_VERSION`         | API version                            | e.g., `2023-05-15`                                |
     | `OPENAI_DEPLOYMENT_NAME`     | *Your deployment name*                 | Name of your deployed OpenAI model                |
     | `CORS_ORIGINS`               | Frontend URL(s)                        | e.g., `https://your-frontend.azurestaticapps.net` |
     | `VECTOR_SEARCH_ENABLED`      | `true` or `false`                      | Enable if using vector search                     |
     | `VECTOR_SEARCH_ENDPOINT`     | *Your Cognitive Search endpoint*       | Required if vector search is enabled              |
     | `VECTOR_SEARCH_KEY`          | *Your Cognitive Search API key*        | Required if vector search is enabled              |
     | `VECTOR_SEARCH_INDEX`        | *Your index name*                      | Required if vector search is enabled              |
     | `SYSTEM_PROMPT`              | *Custom system prompt*                 | Optional                                          |

3. **Set Up GitHub Secrets**:

   In your GitHub repository, add the following secrets:

   - **Required Secrets**:

     | Secret Name                      | Value                                      |
     |----------------------------------|--------------------------------------------|
     | `AZURE_CREDENTIALS`              | Azure service principal credentials (JSON) |
     | `WEBAPP_NAME`                    | Your App Service name                      |
     | `RESOURCE_GROUP`                 | Your Resource Group name                   |
     | `APP_NAME`                       | Same as `APP_NAME` in app settings         |
     | `OPENAI_API_KEY`                 | *Your OpenAI API key*                      |
     | `OPENAI_API_BASE`                | *Your OpenAI API endpoint*                 |
     | `OPENAI_API_VERSION`             | API version                                |
     | `OPENAI_DEPLOYMENT_NAME`         | *Your deployment name*                     |
     | `CORS_ORIGINS`                   | Frontend URL(s)                            |
     | `AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND` | App Service publish profile       |

   - **Optional Secrets** (if using vector search):

     | Secret Name                      | Value                                     |
     |----------------------------------|-------------------------------------------|
     | `VECTOR_SEARCH_ENABLED`          | `true`                                    |
     | `VECTOR_SEARCH_ENDPOINT`         | *Your Cognitive Search endpoint*          |
     | `VECTOR_SEARCH_KEY`              | *Your Cognitive Search API key*           |
     | `VECTOR_SEARCH_INDEX`            | *Your index name*                         |

   - **Create Azure Credentials**:

     Run the following command in Azure CLI to create a service principal:

     ```bash
     az ad sp create-for-rbac --name "myApp" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} --sdk-auth
     ```

     Replace `{subscription-id}` and `{resource-group}` with your details. Copy the JSON output to the `AZURE_CREDENTIALS` secret.

   - **Get Publish Profile**:

     In the App Service, go to **Get publish profile** and copy its content to `AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND`.

4. **Configure GitHub Actions Workflow**:

   - Verify that the workflow file `.github/workflows/backend-deploy.yml` is set up correctly.
   - Ensure it uses the secrets you've added.

5. **Deploy the Backend**:

   - Push changes to the `main` branch.
   - GitHub Actions will trigger and deploy the backend to Azure App Service.

#### Frontend Deployment (Azure Static Web Apps)

1. **Create an Azure Static Web App**:

   - In the Azure Portal, create a new **Static Web App**.
   - Choose **Other** as the deployment source.
   - Note the **Static Web App name**.

2. **Set Up GitHub Secrets**:

   - Add the following secrets to your GitHub repository:

     | Secret Name                       | Value                                         |
     |-----------------------------------|-----------------------------------------------|
     | `AZURE_STATIC_WEB_APPS_API_TOKEN` | Deployment token from Static Web App          |
     | `APP_NAME`                        | Your application name                         |
     | `API_URL`                         | Backend API URL                               |
     | `WS_URL`                          | Backend WebSocket URL (e.g., `wss://.../ws`)  |
     | `MAX_RECONNECT_ATTEMPTS`          | Number of reconnect attempts (optional)       |
     | `DEFAULT_MAX_TOKENS`              | Default max tokens (optional)                 |
     | `DEFAULT_TEMPERATURE`             | Default temperature setting (optional)        |
     | `MESSAGE_HISTORY_LIMIT`           | Message history limit (optional)              |

   - **Get Deployment Token**:

     In the Static Web App, go to **Manage deployment token** and copy it to `AZURE_STATIC_WEB_APPS_API_TOKEN`.

3. **Configure GitHub Actions Workflow**:

   - Ensure `.github/workflows/frontend-deploy.yml` is configured with the correct secrets.
   - The workflow will build and deploy the frontend.

4. **Deploy the Frontend**:

   - Push changes to the `main` branch.
   - GitHub Actions will trigger and deploy the frontend to Azure Static Web Apps.

#### Post-Deployment Configuration

1. **Update Backend CORS Settings**:

   - In the App Service, update **CORS** settings to include your frontend URL.

2. **Verify the Application**:

   - Visit your frontend URL to test the application.
   - Ensure that the chat functionality works as expected.

## Disclaimer

This application is unstable and in the early stages of development. Features and configurations are subject to change without notice.