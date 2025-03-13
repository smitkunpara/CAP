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
    if (analyzeButton) analyzeButton.addEventListener('click', analyzeEmail);
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

const analyzeEmail = () => {
    const resultsDiv = document.getElementById('results');

    // Show the results div
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = 'Analyzing email...';

    // Get the current tab to access the URL
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
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
                const result = await chrome.storage.local.get(['userToken']);
                const userToken = result.userToken;
                let response = await fetch("http://localhost:8000/email", {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${userToken}`,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ email_id: messageId }),
                });
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                }

                const data = await response.json();
                resultsDiv.innerHTML = `
                    <h3>Analysis Results:</h3>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                `;
            } catch (error) {
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