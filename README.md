# Email Security Analyzer Chrome Extension

This project is a Chrome extension that helps users identify potentially dangerous emails and phishing attempts. It analyzes emails in real-time and provides warnings when suspicious content or potential security threats are detected.

## Key Features

- Real-time email content analysis
- Phishing detection and warnings
- Security threat identification
- User-friendly browser extension interface
- Secure backend processing of email content
- Privacy-focused email analysis

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- MongoDB database
- Google Cloud Platform account (for OAuth)
- Git (for version control)

## Setup Instructions

### 1. Virtual Environment Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# For Windows
venv\Scripts\activate
# For Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

1. Create a `.env` file in the root directory
2. Add the following required variables:
   ```
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="your-google-client-secret"
   GOOGLE_REFRESH_TOKEN="your-google-refresh-token"
   
   # JWT Configuration
   JWT_SECRET="your-secure-jwt-secret"
   JWT_ALGORITHM="your-jwt-algorithm"
   JWT_EXP_MINUTES="your-jwt-expiration-minutes"
   
   # MongoDB Configuration
   DATABASE_URL="your-mongodb-connection-string"
   DATABASE_NAME="your-database-name"
   ```

### 3. Chrome Extension Setup

1. Open Google Chrome
2. Enable Developer Mode:
   - Go to `chrome://extensions/`
   - Toggle "Developer mode" in the top right corner
3. Load the extension:
   - Click "Load unpacked"
   - Select the `frontend` directory from this project
   - The extension icon should appear in your Chrome toolbar

### 4. Running the Project

1. Make sure your virtual environment is activated
2. Start the backend server:
   ```bash
   python main.py
   ```
3. The server should start running on the configured port
4. The Chrome extension will automatically connect to the backend server

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Submit a pull request with your changes
