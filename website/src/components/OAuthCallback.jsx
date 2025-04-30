import { useEffect } from 'react';

const OAuthCallback = () => {
  useEffect(() => {
    // Function to get the code from URL
    function getCodeFromUrl() {
      const urlParams = new URLSearchParams(window.location.search);
      return urlParams.get('code');
    }

    // Get the authorization code
    const code = getCodeFromUrl();
    
    if (code) {
      // Send the code to the parent window that opened this popup
      if (window.opener) {
        window.opener.postMessage({
          type: 'oauth-response',
          code: code
        }, window.location.origin);
        
        // Close the popup window
        window.close();
      }
    }
  }, []);

  return (
    <div className="oauth-callback">
      <h2>Authentication successful</h2>
      <p>Please wait while we complete the process...</p>
    </div>
  );
};

export default OAuthCallback;