document.addEventListener('DOMContentLoaded', () => {
    const analyzeButton = document.getElementById('analyzeBtn');
    analyzeButton.addEventListener('click', analyzeEmail);
});

const analyzeEmail = () => {
    const current_uri = window.location.href;
    const resultsDiv = document.getElementById('results');
    
    // Show the results div and display loading message
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = 'Analyzing email...';

    fetch("http://localhost:8000/email", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email_link: current_uri }),
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
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
                </p>
            `;
        });
};