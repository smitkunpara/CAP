async function isTokenValid(token) {
    try {
        const response = await fetch("http://localhost:8000/auth/validate", {
            method: "GET",
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        if (response.ok) {
            return true;
        }
        return false;
    } catch (error) {
        return false;
    }
}

async function checkAuthStatus() {
    try {
        // chrome.storage.local.set({
        //     userToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InNtaXRrdW1hcl9rdW5wYXJhQHNybWFwLmVkdS5pbiIsIm5hbWUiOiJTbWl0a3VtYXIgS3VucGFyYSB8IEFQMjExMTAwMTEyNzUiLCJleHAiOjE3NDE4MDQ1NTR9.D2YPXsuhICLNZ-wyz7KlK-lssumKJHN-oHbdsX46-rw"
        // });
        const result = await new Promise(resolve => {
            chrome.storage.local.get(['userToken'], resolve);
        });

        if (result.userToken) {
            const isValid = await isTokenValid(result.userToken);
            if (isValid) {
                showAnalyzerSection();
                return;
            } else {
                // console.error("token is invalid");
                await handleLogout(false);
            }
        }
        // If we get here, either no token or invalid token
        hideAnalyzerSection();
    } catch (error) {
        let resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <p style="color: red;">
                Failed to check auth status. Please try again later.
                <br>
                Error: ${error.message}
            </p>
        `;
        hideAnalyzerSection();
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await checkAuthStatus();
    const loginButton = document.getElementById('loginBtn');
    const analyzeButton = document.getElementById('analyzeBtn');
    const logoutButton = document.getElementById('logoutBtn');

    if (loginButton) loginButton.addEventListener('click', handleLogin);
    if (analyzeButton) analyzeButton.addEventListener('click', () => {
        // Send message to content script to analyze email
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "analyzeEmail"});
        });
    });
    if (logoutButton) logoutButton.addEventListener('click', handleLogout);
});

function handleLogin() {
    chrome.identity.getAuthToken({
        interactive: true
    }, function (accessToken) {
        if (chrome.runtime.lastError) {
            const errorMessage = chrome.runtime.lastError.message || 'Unknown error occurred';
            alert(`Authentication failed: ${errorMessage}`);
            return;
        }

        // Get refresh token from Chrome identity API
        chrome.identity.getProfileUserInfo(function (userInfo) {
            // Send both access token and refresh token to your backend
            fetch("http://localhost:8000/auth/google", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token: accessToken
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
                    chrome.storage.local.set({
                        userToken: data.token,
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

async function handleLogout(sendrequest = true) {
    try {
        // Get the stored token
        const result = await chrome.storage.local.get(['userToken']);
        const userToken = result.userToken;
        // Send logout request to backend
        if (sendrequest) {
            const response = await fetch('http://localhost:8000/auth/logout', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${userToken}`
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        }
        await chrome.storage.local.remove(['userToken']);
        // remove the results div
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'none';
        hideAnalyzerSection();
        alert('Logged out successfully');

    } catch (error) {
        console.error("error",error);
    }
}

function showAnalyzerSection() {
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('analyzerSection').style.display = 'flex';
}

function hideAnalyzerSection() {
    document.getElementById('loginSection').style.display = 'flex';
    document.getElementById('analyzerSection').style.display = 'none';
}

