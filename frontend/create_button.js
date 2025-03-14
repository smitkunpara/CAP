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
        button.addEventListener("click", window.analyzeEmail);
        targetDiv.appendChild(button);
    } else {
        console.log("not in email view");
    }
}

function initObserver() {
    if (isEmailView()) {
        setTimeout(injectButton, 100);
    }
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