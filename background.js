// Background script for Sponsor Sniper

console.log('Sponsor Sniper background script initialized');

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background script received message:', request);
  
  // Handle message types
  if (request.type === 'fetchSponsorSegments') {
    const videoId = request.videoId;
    console.log('Fetching sponsor segments for video:', videoId);
    
    // Fetch segments from backend
    fetch(`http://localhost:8080/sponsors?v=${videoId}&threshold=0.3`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Sponsor segments fetched successfully:', data);
        sendResponse({ success: true, data: data });
      })
      .catch(error => {
        console.error('Error fetching sponsor segments:', error);
        sendResponse({ success: false, error: error.message });
      });
    
    // Return true to indicate that the response will be sent asynchronously
    return true;
  }
  
  // Ping the backend server to check connection
  if (request.type === 'pingBackend') {
    console.log('Pinging backend server');
    
    fetch('http://localhost:8080/ping')
      .then(response => response.json())
      .then(data => {
        console.log('Backend ping response:', data);
        sendResponse({ success: true, data: data });
      })
      .catch(error => {
        console.error('Error pinging backend:', error);
        sendResponse({ success: false, error: error.message });
      });
    
    return true;
  }
}); 