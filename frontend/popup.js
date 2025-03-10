let userToken = null;
let refreshToken = null;

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

// Function to refresh the access token
async function refreshAccessToken() {
    try {
        const response = await fetch("http://localhost:8000/auth/refresh", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            throw new Error('Failed to refresh token');
        }

        const data = await response.json();
        return data.access_token;
    } catch (error) {
        console.error('Error refreshing token:', error);
        throw error;
    }
}

// Function to check authentication status
async function checkAuthStatus() {
    try {
        const result = await new Promise(resolve => {
            chrome.storage.local.get(['userToken', 'refreshToken'], resolve);
        });

        if (result.userToken) {
            const isValid = await isTokenValid(result.userToken);
            if (isValid) {
                userToken = result.userToken;
                refreshToken = result.refreshToken;
                showAnalyzerSection();
                return;
            } else {
                // Try to refresh the token
                try {
                    const newAccessToken = await refreshAccessToken();
                    userToken = newAccessToken;
                    await chrome.storage.local.set({ userToken: newAccessToken });
                    showAnalyzerSection();
                    return;
                } catch (error) {
                    console.error('Failed to refresh token:', error);
                    await handleLogout();
                }
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
    }, function (accessToken) {
        if (chrome.runtime.lastError) {
            const errorMessage = chrome.runtime.lastError.message || 'Unknown error occurred';
            console.error('Authentication error:', errorMessage);
            alert(`Authentication failed: ${errorMessage}`);
            return;
        }

        // Get refresh token from Chrome identity API
        chrome.identity.getProfileUserInfo(function(userInfo) {
            // Send both access token and refresh token to your backend
            fetch("http://localhost:8000/auth/google", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    token: accessToken,
                    refresh_token: userInfo.id // This is a simplified example, you'll need to get the actual refresh token
                })
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
                refreshToken = data.refresh_token;
                // Store both tokens
                chrome.storage.local.set({ 
                    userToken: data.token,
                    refreshToken: data.refresh_token
                });
                showAnalyzerSection();
            })
            .catch(error => {
                console.error('Error during authentication:', error);
                alert('Failed to authenticate. Please try again.');
            });
        });
    });
}

// Update handleLogout to be async
async function handleLogout() {
    return new Promise((resolve) => {
        //remove tokens from local storage
        chrome.storage.local.remove(['userToken', 'refreshToken'], () => {
            hideAnalyzerSection();
            resolve();
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
    const resultsDiv = document.getElementById('results');

    // Show the results div
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = 'Analyzing email...';

    // Get the current tab to access the URL
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const activeTab = tabs[0];
        const url = activeTab.url;

        // Check if we're on Gmail
        if (!url.includes('mail.google.com')) {
            resultsDiv.innerHTML = `
                <p style="color: red;">
                    Please open a Gmail email to analyze.
                </p>
            `;
            return;
        }

        // Execute script in the context of the Gmail page to get the message ID
        chrome.scripting.executeScript({
            target: { tabId: activeTab.id },
            func: () => {
                let messageId = null;
                // Try first selector
                let v1 = document.querySelector("#\\:1 > div > div:nth-child(3) > div > div.nH.a98.iY > div:nth-child(1) > div > div:nth-child(2) > div.ha > h2");
                if (v1) {
                    messageId = v1.getAttribute("data-legacy-thread-id");
                } else {
                    // Try second selector
                    let v2 = document.querySelector("#\\:1 > div > div:nth-child(1) > div > div.nH.a98.iY > div:nth-child(1) > div > div:nth-child(2) > div.ha > h2");
                    if (v2) {
                        messageId = v2.getAttribute("data-legacy-thread-id");
                    }
                }
                return messageId;
            }
        }, async (results) => {
            const messageId = results[0].result;
            
            if (!messageId) {
                resultsDiv.innerHTML = `
                    <p style="color: red;">
                        Could not find email ID. Please make sure you're viewing a specific email in Gmail.
                    </p>
                `;
                return;
            }

            try {
                let response = await fetch("http://localhost:8000/email", {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${userToken}`,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ email_id: messageId }),
                });

                if (response.status === 401) {
                    // Token expired, try to refresh
                    try {
                        const newAccessToken = await refreshAccessToken();
                        userToken = newAccessToken;
                        await chrome.storage.local.set({ userToken: newAccessToken });
                        
                        // Retry the request with new token
                        response = await fetch("http://localhost:8000/email", {
                            method: "POST",
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${newAccessToken}`,
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify({ email_id: messageId }),
                        });
                    } catch (error) {
                        // If refresh fails, logout user
                        await handleLogout();
                        throw new Error('Authentication expired. Please login again.');
                    }
                }

                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                }

                const data = await response.json();
                console.log('Analysis successful:', data);
                // Format and display the results
                resultsDiv.innerHTML = `
                    <h3>Analysis Results:</h3>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
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
            }
        });
    });
};