let userToken = null;

// Function to validate JWT token
async function isTokenValid(token) {
    try {
        console.log('Validating token...');
        const response = await fetch("http://localhost:8000/auth/validate", {
            method: "GET",
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            console.log('Token validation failed:', response.status);
            return false;
        }
        
        const data = await response.json();
        console.log('Token validation successful:', data);
        return true;
    } catch (error) {
        console.error('Token validation error:', error);
        return false;
    }
}

// Function to check authentication status
async function checkAuthStatus() {
    try {
        const result = await new Promise(resolve => {
            chrome.storage.local.get(['userToken'], resolve);
        });
        
        if (result.userToken) {
            const isValid = await isTokenValid(result.userToken);
            if (isValid) {
                userToken = result.userToken;
                showAnalyzerSection();
                return;
            } else {
                // Token is invalid, clean up
                await handleLogout();
            }
        }
        // If we get here, either no token or invalid token
        hideAnalyzerSection();
    } catch (error) {
        console.error('Auth status check error:', error);
        hideAnalyzerSection();
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Popup opened - checking auth status...');
    
    // First check auth status before setting up UI
    await checkAuthStatus();
    
    // Then setup button listeners
    const loginButton = document.getElementById('loginBtn');
    const analyzeButton = document.getElementById('analyzeBtn');
    const logoutButton = document.getElementById('logoutBtn');
    
    if (loginButton) loginButton.addEventListener('click', handleLogin);
    if (analyzeButton) analyzeButton.addEventListener('click', analyzeEmail);
    if (logoutButton) logoutButton.addEventListener('click', handleLogout);
});

function handleLogin() {
    chrome.identity.getAuthToken({ 
        interactive: true
    }, function(accessToken) {
        if (chrome.runtime.lastError) {
            const errorMessage = chrome.runtime.lastError.message || 'Unknown error occurred';
            console.error('Authentication error:', errorMessage);
            alert(`Authentication failed: ${errorMessage}`);
            return;
        }

        // Send the access token to your backend
        fetch("http://localhost:8000/auth/google", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token: accessToken })
        })
        .then(async response => {
            if (!response.ok) {
                const text = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
            }
            return response.json();
        })
        .then(data => {
            userToken = data.token;
            // Store the token
            chrome.storage.local.set({ userToken: data.token });
            showAnalyzerSection();
        })
        .catch(error => {
            console.error('Error during authentication:', error);
            alert('Failed to authenticate. Please try again.');
        });
    });
}

// Update handleLogout to be async
async function handleLogout() {
    return new Promise((resolve) => {
        chrome.identity.getAuthToken({ interactive: false }, function(current_token) {
            if (!chrome.runtime.lastError) {
                chrome.identity.removeCachedAuthToken({ token: current_token }, function() {
                    chrome.identity.clearAllCachedAuthTokens(function() {
                        userToken = null;
                        chrome.storage.local.remove('userToken', () => {
                            hideAnalyzerSection();
                            resolve();
                        });
                    });
                });
            } else {
                hideAnalyzerSection();
                resolve();
            }
        });
    });
}

function showAnalyzerSection() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('analyzerSection').style.display = 'flex';
}

function hideAnalyzerSection() {
    document.getElementById('loginSection').style.display = 'flex';
    document.getElementById('analyzerSection').style.display = 'none';
}

const analyzeEmail = () => {
    const current_uri = window.location.href;
    const resultsDiv = document.getElementById('results');
    
    // Show the results div and display loading message
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = 'Analyzing email...';

    console.log('Attempting to analyze email with URI:', current_uri);
    console.log('Using userToken:', userToken ? 'Token exists' : 'No token');

    fetch("http://localhost:8000/email", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userToken}`,
            'Accept': 'application/json'
        },
        body: JSON.stringify({ email_link: current_uri }),
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            if (response.status === 401) {
                // Token expired or invalid
                handleLogout();
                throw new Error('Authentication expired. Please login again.');
            }
            return response.text().then(text => {
                throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Analysis successful:', data);
        // Format and display the results
        resultsDiv.innerHTML = `
            <h3>Analysis Results:</h3>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
    })
    .catch(error => {
        console.error('Error analyzing email:', error);
        resultsDiv.innerHTML = `
            <p style="color: red;">
                Failed to analyze email. Please try again later.
                <br>
                Error: ${error.message}
                <br>
                <small>Check the console for more details (Right-click > Inspect)</small>
            </p>
        `;
    });
};