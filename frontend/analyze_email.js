const get_mail_id = () => {
    let messageId = null;
    let v1 = document.querySelector("#\\:1 > div > div:nth-child(3) > div > div.nH.a98.iY > div:nth-child(1) > div > div:nth-child(2) > div.ha > h2");
    if (v1) {
        messageId = v1.getAttribute("data-legacy-thread-id");
    } else {
        let v2 = document.querySelector("#\\:1 > div > div:nth-child(1) > div > div.nH.a98.iY > div:nth-child(1) > div > div:nth-child(2) > div.ha > h2");
        if (v2) {
            messageId = v2.getAttribute("data-legacy-thread-id");
        }
    }
    return messageId;
}

window.analyzeEmail = async () => {
    const messageId = get_mail_id();
    if (!messageId) {
        alert("Could not find email ID. Please make sure you're viewing a specific email in Gmail.");
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
        alert(JSON.stringify(data, null, 2));
    } catch (error) {
        alert(error.message);
    }
};

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyzeEmail") {
        window.analyzeEmail();
    }
}); 
