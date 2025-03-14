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
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "analyzeEmail"});
        });
    });
    if (logoutButton) logoutButton.addEventListener('click', handleLogout);
});

function handleLogin() {
    const manifest = chrome.runtime.getManifest();
    const clientId = manifest.oauth2.client_id;
    const redirectUri = chrome.identity.getRedirectURL();
    
    console.log("Using redirect URI:", redirectUri);
    
    const scope = manifest.oauth2.scopes.join(" ");
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${clientId}&` +
    `redirect_uri=${encodeURIComponent(redirectUri)}&` +
    `response_type=code&` +
    `scope=${encodeURIComponent(scope)}&` +
    `access_type=offline&` +
    `prompt=consent`;
    
    console.log("Auth URL:", authUrl);
    
    chrome.identity.launchWebAuthFlow(
        {
            url: authUrl,
            interactive: true
        },
        function (redirectUrl) {
            if (chrome.runtime.lastError) {
                console.error("Chrome runtime error:", chrome.runtime.lastError);
                alert(`Authentication failed: ${chrome.runtime.lastError.message}`);
                return;
            }

            if (!redirectUrl) {
                console.error("No redirect URL received");
                alert("Authentication failed: No response from Google");
                return;
            }

            // Extract authorization code from redirect URL
            const urlParams = new URLSearchParams(new URL(redirectUrl).search);
            const authCode = urlParams.get("code");

            if (!authCode) {
                console.error("No auth code in redirect URL:", redirectUrl);
                alert("Failed to retrieve authorization code.");
                return;
            }

            // Send authorization code to backend
            fetch("http://localhost:8000/auth/google", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: authCode,
                    redirect_uri: redirectUri  // Important: Send the same redirect URI used in the initial request
                }),
            })
            .then(async (response) => {
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                }
                return response.json();
            })
            .then((data) => {
                chrome.storage.local.set({
                    userToken: data.jwt_token
                });
                showAnalyzerSection();
                alert("Login successful!");
            })
            .catch((error) => {
                console.error("Error during authentication:", error);
                alert("Failed to authenticate. Please try again.");
            });
        }
    );
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

