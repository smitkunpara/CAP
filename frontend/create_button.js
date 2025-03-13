function isEmailView() {
    return window.location.href.includes('/mail/') &&
        (window.location.hash.includes('#inbox/') ||
            window.location.hash.includes('#all/') ||
            window.location.hash.includes('#sent/'));
}

function injectButton() {
    let targetDiv = document.querySelector("#\\:1 > div > div:nth-child(1) > div > div.nH.a98.iY > div:nth-child(1) > div > div:nth-child(2) > div.ha > span") || document.querySelector("#\\:1 > div > div:nth-child(3) > div > div.nH.a98.iY > div:nth-child(1) > div > div:nth-child(2) > div.ha > span");
    if (targetDiv) {
        if (document.getElementById("custom-gmail-button")) {
            return;
        }
        const button = document.createElement("button");
        button.className = "aau";
        button.id = "custom-gmail-button";
        button.textContent = "analyze this email";
        button.style.backgroundColor = "#4285f4";
        button.style.color = "white";
        button.style.cursor = "pointer";
        button.addEventListener("click", ()=>alert("clicked"));
        targetDiv.appendChild(button);
    } else {
        console.log("not in email view");
    }
}

function initObserver() {
    if (isEmailView()) {
        setTimeout(injectButton, 100);
    }

    // const observer = new MutationObserver((mutations) => {
    //     if (isEmailView() && !document.getElementById("custom-gmail-button")) {
    //         setTimeout(injectButton, 100);
    //     }
    // });

    // observer.observe(document.body, {
    //     childList: true,
    //     subtree: true
    // });
    window.addEventListener('hashchange', () => {
        if (isEmailView()) {
            setTimeout(injectButton, 100);
        }
    });
}
if (document.readyState === "complete") {
    initObserver();
} else {
    window.addEventListener('load', initObserver);
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
