// Content script for Sponsor Sniper extension
// This script runs on YouTube pages and handles the sponsor skipping functionality

console.log('Sponsor Sniper initialized');

// Default settings
let settings = {
  enableSkipping: true,
  showNotifications: true,
  debugMode: true  // Enable debug mode by default
};

// Store detected sponsor segments
let currentVideoId = null;
let sponsorSegments = [];
let lastSkipTime = 0;
let hasSetupSkipListener = false;

// Load settings from storage
function loadSettings() {
  chrome.storage.sync.get(
    {
      enableSkipping: true,
      showNotifications: true,
      debugMode: true  // Enable debug mode by default
    },
    function(items) {
      settings = items;
      console.log('Settings loaded:', settings);
      if (settings.debugMode) {
        createDebugOverlay();
      }
    }
  );
}

// Listen for settings changes
chrome.storage.onChanged.addListener(function(changes) {
  for (const key in changes) {
    settings[key] = changes[key].newValue;
  }
  console.log('Settings updated:', settings);
});

// Function to check if we're on a YouTube watch page
function isYouTubeWatchPage() {
  return window.location.pathname.includes('/watch');
}

// Function to extract video ID from URL
function getVideoId() {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('v');
}

// Function to communicate with backend API to get sponsor segments
async function getSponsorSegments(videoId) {
  console.log(`Fetching sponsor segments for video: ${videoId}`);
  
  try {
    // Method 1: Try using the background script to fetch segments
    console.log('Requesting segments via background script');
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: 'fetchSponsorSegments', videoId: videoId }, response => {
        console.log('Background script response:', response);
        
        if (response && response.success && response.data && response.data.sponsors) {
          console.log(`Found ${response.data.sponsors.length} sponsor segments via background script`);
          
          // Process segments to ensure they have proper numerical values
          const processedSegments = response.data.sponsors.map(segment => ({
            startTime: parseFloat(segment.startTime),
            endTime: parseFloat(segment.endTime),
            duration: parseFloat(segment.endTime) - parseFloat(segment.startTime)
          }));
          
          console.log('Processed segments:', processedSegments);
          resolve(processedSegments);
        } else {
          console.error('Failed to get segments from background script, trying direct fetch');
          // If background script fails, try direct fetch (Method 2)
          fetchDirectly(videoId)
            .then(segments => resolve(segments))
            .catch(error => {
              console.error('All fetch methods failed:', error);
              resolve([]);
            });
        }
      });
    });
  } catch (error) {
    console.error('Error in getSponsorSegments:', error);
    // Try the direct approach as fallback
    return fetchDirectly(videoId);
  }
}

// Helper function to fetch directly from the API
async function fetchDirectly(videoId) {
  console.log('Attempting direct fetch...');
  try {
    // Connect to our backend API to get sponsor segments
    const url = `http://localhost:8080/sponsors?v=${videoId}&threshold=0.3`;
    console.log(`Requesting: ${url}`);
    
    // Use XHR for more direct control
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.setRequestHeader('Accept', 'application/json');
      
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            console.log('XHR success, response:', data);
            
            if (!data.success) {
              console.error('API error:', data.error || 'Unknown error');
              resolve([]);
              return;
            }
            
            if (!data.sponsors || !Array.isArray(data.sponsors) || data.sponsors.length === 0) {
              console.log('No sponsor segments found via XHR');
              resolve([]);
              return;
            }
            
            // Process segments
            const processedSegments = data.sponsors.map(segment => ({
              startTime: parseFloat(segment.startTime),
              endTime: parseFloat(segment.endTime),
              duration: parseFloat(segment.endTime) - parseFloat(segment.startTime)
            }));
            
            console.log('XHR processed segments:', processedSegments);
            resolve(processedSegments);
          } catch (e) {
            console.error('Error parsing XHR response:', e);
            console.error('XHR raw response:', xhr.responseText);
            resolve([]);
          }
        } else {
          console.error('XHR error:', xhr.status, xhr.statusText);
          resolve([]);
        }
      };
      
      xhr.onerror = function() {
        console.error('XHR network error');
        resolve([]);
      };
      
      xhr.send();
    });
  } catch (error) {
    console.error('Error in direct fetch:', error);
    return [];
  }
}

// Function to show notification when skipping a sponsor
function showSkipNotification(skipStartTime, skipEndTime) {
  if (!settings.showNotifications) return;
  
  // Create or get notification element
  let notification = document.getElementById('sponsor-sniper-notification');
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'sponsor-sniper-notification';
    notification.style.cssText = `
      position: fixed;
      bottom: 70px;
      right: 20px;
      background-color: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 10px 15px;
      border-radius: 4px;
      z-index: 9999;
      font-family: Arial, sans-serif;
      font-size: 14px;
      transition: opacity 0.3s;
      opacity: 0;
    `;
    document.body.appendChild(notification);
  }
  
  // Format the skip duration for display (round to 1 decimal place)
  const durationSecs = skipEndTime - skipStartTime;
  const durationText = durationSecs >= 60 
    ? `${Math.floor(durationSecs / 60)}m ${Math.round(durationSecs % 60)}s` 
    : `${durationSecs.toFixed(1)}s`;
  
  // Format the timestamp for display
  const formatTimestamp = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Set notification text and show it
  notification.innerHTML = `
    <div>Sponsor skipped</div>
    <div style="font-size: 12px; opacity: 0.9; margin-top: 3px;">
      ${formatTimestamp(skipStartTime)} - ${formatTimestamp(skipEndTime)} (${durationText})
    </div>
  `;
  notification.style.opacity = '1';
  
  // Hide notification after 3 seconds
  setTimeout(() => {
    notification.style.opacity = '0';
  }, 3000);
}

// Function to skip to a specific time in the video (improved version)
function skipToTime(seconds, startTime) {
  const videoElement = document.querySelector('video');
  if (!videoElement) {
    console.error('Video element not found for skipping');
    return;
  }
  
  // Don't skip if we've recently skipped (to prevent skipping loops)
  const now = Date.now();
  if (now - lastSkipTime < 1000) {
    console.log('Skipping too frequent, ignoring');
    return;
  }
  
  lastSkipTime = now;
  console.log(`Skipping from ${startTime}s to ${seconds}s`);
  
  // Method 1: Try direct currentTime setting
  videoElement.currentTime = seconds;
  
  // Method 2: Try injecting a script to use YouTube's API (more reliable)
  try {
    // Create and inject a script to control the YouTube player
    const script = document.createElement('script');
    script.textContent = `
      (function() {
        try {
          // Try to get the YouTube player instance
          const player = document.querySelector('video');
          if (player) {
            // Force seek to specific time
            player.currentTime = ${seconds};
            
            // Try to use YouTube's API if available
            if (window.yt && window.yt.player && window.yt.player.getPlayerByElement) {
              const ytPlayer = window.yt.player.getPlayerByElement(player);
              if (ytPlayer && ytPlayer.seekTo) {
                ytPlayer.seekTo(${seconds}, true);
              }
            }
          }
        } catch (e) {
          console.error('Error in injected skip script:', e);
        }
      })();
    `;
    document.body.appendChild(script);
    script.remove(); // Clean up after execution
  } catch (e) {
    console.error('Error injecting skip script:', e);
  }
  
  showSkipNotification(startTime, seconds);
}

// Debug overlay to visualize sponsor segments
function createDebugOverlay() {
  // Remove existing debug overlay if present
  const existingOverlay = document.getElementById('sponsor-sniper-debug');
  if (existingOverlay) {
    existingOverlay.remove();
  }
  
  // Create debug overlay
  const debugOverlay = document.createElement('div');
  debugOverlay.id = 'sponsor-sniper-debug';
  debugOverlay.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 10px;
    border-radius: 4px;
    z-index: 9999;
    font-family: Arial, sans-serif;
    font-size: 12px;
    max-width: 300px;
    max-height: 200px;
    overflow-y: auto;
  `;
  
  document.body.appendChild(debugOverlay);
  updateDebugOverlay();
}

// Update debug overlay with current state
function updateDebugOverlay() {
  if (!settings.debugMode) return;
  
  const debugOverlay = document.getElementById('sponsor-sniper-debug');
  if (!debugOverlay) return;
  
  const videoElement = document.querySelector('video');
  const currentTime = videoElement ? videoElement.currentTime : 'N/A';
  
  // Format time values for display
  const formatTime = (seconds) => {
    if (seconds === 'N/A') return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Basic info section
  let debugHtml = `
    <div style="border-bottom: 1px solid #444; padding-bottom: 5px; margin-bottom: 5px;">
      <strong>Sponsor Sniper</strong>
      <span style="float: right; font-size: 10px;">${currentVideoId || 'No Video'}</span>
    </div>
    <div>Time: <strong>${formatTime(currentTime)}</strong> (${currentTime !== 'N/A' ? currentTime.toFixed(1) + 's' : 'N/A'})</div>
    <div>Status: ${hasSetupSkipListener ? 
      '<span style="color: #4CAF50;">Active</span>' : 
      '<span style="color: #F44336;">Inactive</span>'}</div>
    <div>Auto-Skip: ${settings.enableSkipping ? 
      '<span style="color: #4CAF50;">Enabled</span>' : 
      '<span style="color: #F44336;">Disabled</span>'}</div>
    <div>Detected: <strong>${sponsorSegments.length}</strong> segment${sponsorSegments.length !== 1 ? 's' : ''}</div>
  `;
  
  // Add segments section if we have any
  if (sponsorSegments.length > 0) {
    debugHtml += `
      <div style="border-top: 1px solid #444; margin-top: 5px; padding-top: 5px;">
        <strong>Sponsor Segments:</strong>
      </div>
    `;
    
    sponsorSegments.forEach((segment, index) => {
      const isActive = videoElement && 
                       currentTime >= segment.startTime && 
                       currentTime < segment.endTime;
      
      // Format duration
      const duration = segment.endTime - segment.startTime;
      const durationText = duration >= 60 
        ? `${Math.floor(duration / 60)}m ${Math.round(duration % 60)}s` 
        : `${duration.toFixed(1)}s`;
      
      // Calculate progress through segment (if currently in one)
      let progressBar = '';
      if (isActive) {
        const progress = (currentTime - segment.startTime) / (segment.endTime - segment.startTime);
        const progressPercent = Math.min(100, Math.max(0, progress * 100));
        
        progressBar = `
          <div style="height: 4px; background: #333; margin-top: 3px; border-radius: 2px; overflow: hidden;">
            <div style="width: ${progressPercent}%; height: 100%; background: #F44336;"></div>
          </div>
        `;
      }
      
      const style = isActive 
        ? 'background: rgba(255, 0, 0, 0.2); border-left: 3px solid #F44336; padding-left: 5px;' 
        : '';
      
      debugHtml += `
        <div style="${style} margin: 3px 0; padding: 2px 0;">
          <span style="color: ${isActive ? '#F44336' : '#FFC107'};">
            ${index + 1}: ${formatTime(segment.startTime)} - ${formatTime(segment.endTime)}
          </span>
          <span style="float: right; font-size: 11px; color: #AAA;">${durationText}</span>
          ${progressBar}
        </div>
      `;
    });
  } else {
    debugHtml += '<div style="color: #FFC107; margin-top: 5px;">No sponsor segments detected</div>';
  }
  
  // Add test button at bottom
  debugHtml += `
    <div style="margin-top: 10px; text-align: center;">
      <button id="sponsor-sniper-test-fetch" style="background: #444; color: white; border: none; padding: 3px 8px; border-radius: 3px; cursor: pointer; font-size: 10px;">
        Test Fetch
      </button>
    </div>
  `;
  
  debugOverlay.innerHTML = debugHtml;
  
  // Add event listener to the test fetch button
  const testFetchButton = document.getElementById('sponsor-sniper-test-fetch');
  if (testFetchButton) {
    testFetchButton.addEventListener('click', () => {
      console.log('Test fetch button clicked');
      if (currentVideoId) {
        testDirectFetch(currentVideoId);
      } else {
        const videoId = getVideoId();
        if (videoId) {
          testDirectFetch(videoId);
        } else {
          console.error('No video ID found for test fetch');
        }
      }
    });
  }
}

// Function to test direct fetch to backend
function testDirectFetch(videoId) {
  console.log('Testing direct fetch for video:', videoId);
  
  // Add a status message to the debug overlay
  const debugOverlay = document.getElementById('sponsor-sniper-debug');
  if (debugOverlay) {
    const statusDiv = document.createElement('div');
    statusDiv.style.color = 'yellow';
    statusDiv.textContent = 'Fetching segments...';
    debugOverlay.appendChild(statusDiv);
    
    // Update the status with fetch results
    updateStatus = (message, color) => {
      statusDiv.textContent = message;
      statusDiv.style.color = color || 'white';
    };
  }
  
  // Try XHR first
  const xhr = new XMLHttpRequest();
  xhr.open('GET', `http://localhost:8080/sponsors?v=${videoId}&threshold=0.3`, true);
  xhr.setRequestHeader('Accept', 'application/json');
  
  xhr.onload = function() {
    console.log('XHR response:', xhr.status, xhr.responseText);
    
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const data = JSON.parse(xhr.responseText);
        console.log('XHR success, parsed data:', data);
        
        if (data.success && data.sponsors && data.sponsors.length > 0) {
          // Process segments
          sponsorSegments = data.sponsors.map(segment => ({
            startTime: parseFloat(segment.startTime),
            endTime: parseFloat(segment.endTime),
            duration: parseFloat(segment.endTime) - parseFloat(segment.startTime)
          }));
          
          // Update the overlay and listener
          updateDebugOverlay();
          if (!hasSetupSkipListener) {
            setupSkipListener();
          }
          
          if (updateStatus) {
            updateStatus(`Loaded ${sponsorSegments.length} segments via XHR`, 'green');
          }
        } else {
          console.log('No segments found in XHR response');
          if (updateStatus) {
            updateStatus('No segments found in response', 'red');
          }
        }
      } catch (e) {
        console.error('Error parsing XHR response:', e);
        if (updateStatus) {
          updateStatus('Error parsing response', 'red');
        }
      }
    } else {
      console.error('XHR error:', xhr.status, xhr.statusText);
      if (updateStatus) {
        updateStatus(`XHR error: ${xhr.status}`, 'red');
      }
    }
  };
  
  xhr.onerror = function() {
    console.error('XHR network error');
    if (updateStatus) {
      updateStatus('Network error', 'red');
    }
  };
  
  xhr.send();
}

// Function to check if the current time is within a sponsor segment and skip it
function checkAndSkipSponsors() {
  if (!settings.enableSkipping || sponsorSegments.length === 0) return;
  
  const videoElement = document.querySelector('video');
  if (!videoElement) return;
  
  const currentTime = videoElement.currentTime;
  
  // Update debug overlay with current state
  if (settings.debugMode) {
    updateDebugOverlay();
  }
  
  // Check if current time is within any sponsor segment
  for (const segment of sponsorSegments) {
    if (currentTime >= segment.startTime && currentTime < segment.endTime) {
      console.log(`Detected sponsor segment at ${currentTime}s (${segment.startTime}s - ${segment.endTime}s)`);
      // Skip to the end of the sponsor segment
      skipToTime(segment.endTime, segment.startTime);
      break;
    }
  }
}

// Function to set up listener for video time updates
function setupSkipListener() {
  if (hasSetupSkipListener) return;
  
  const videoElement = document.querySelector('video');
  if (!videoElement) {
    console.error('Video element not found for setting up listener');
    return;
  }
  
  console.log('Setting up time update listener');
  
  // Use an interval instead of timeupdate event for more reliable checking
  const checkInterval = setInterval(() => {
    if (!document.querySelector('video')) {
      console.log('Video element removed, clearing interval');
      clearInterval(checkInterval);
      hasSetupSkipListener = false;
      return;
    }
    
    checkAndSkipSponsors();
  }, 500);
  
  hasSetupSkipListener = true;
  console.log('Sponsor segment monitoring active');
}

// Main initialization function
async function initialize() {
  console.log('Initializing Sponsor Sniper');
  
  // Immediately test the backend connection
  testBackendConnection();
  
  // Load settings first
  loadSettings();
  
  // Only run on YouTube watch pages
  if (!isYouTubeWatchPage()) {
    console.log('Not a YouTube watch page, exiting');
    return;
  }
  
  // Get the video ID
  const videoId = getVideoId();
  if (!videoId) {
    console.error('Could not determine video ID');
    return;
  }
  
  // Skip if this is the same video we've already processed
  if (videoId === currentVideoId && sponsorSegments.length > 0) {
    console.log('Already processed this video, reusing existing segments');
    setupSkipListener();
    return;
  }
  
  console.log(`Processing YouTube video: ${videoId}`);
  currentVideoId = videoId;
  
  // Fetch sponsor segments from the backend
  sponsorSegments = await getSponsorSegments(videoId);
  
  // Wait for the video element to be ready
  waitForVideoElement();
}

// Test connection to backend server
function testBackendConnection() {
  console.log('Testing backend connection...');
  
  // Try using the background script first
  chrome.runtime.sendMessage({ type: 'pingBackend' }, response => {
    console.log('Backend ping response (via background):', response);
    
    if (response && response.success) {
      console.log('Backend connection successful via background script');
    } else {
      // If background fails, try direct connection
      console.log('Background ping failed, trying direct ping');
      
      // Use XHR for a more direct approach
      const xhr = new XMLHttpRequest();
      xhr.open('GET', 'http://localhost:8080/ping', true);
      
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
          console.log('Direct ping successful:', xhr.responseText);
        } else {
          console.error('Direct ping failed:', xhr.status, xhr.statusText);
        }
      };
      
      xhr.onerror = function() {
        console.error('XHR network error during ping');
      };
      
      xhr.send();
    }
  });
  
  // Also try a simple fetch as another test
  fetch('http://localhost:8080/ping')
    .then(response => {
      console.log('Fetch ping response status:', response.status);
      return response.json();
    })
    .then(data => {
      console.log('Fetch ping data:', data);
    })
    .catch(error => {
      console.error('Fetch ping error:', error);
    });
}

// Function to wait for the video element
function waitForVideoElement() {
  let attempts = 0;
  const checkVideoElement = setInterval(() => {
    const videoElement = document.querySelector('video');
    attempts++;
    
    if (videoElement) {
      clearInterval(checkVideoElement);
      console.log('Video element found, setting up listener');
      setupSkipListener();
    } else if (attempts >= 30) { // 15 seconds max
      clearInterval(checkVideoElement);
      console.error('Video element not found after multiple attempts');
    } else {
      console.log(`Waiting for video element (attempt ${attempts})`);
    }
  }, 500);
}

// Run the extension on page load
console.log('Starting Sponsor Sniper');
initialize();

// Re-run the extension when navigating between YouTube videos (SPA navigation)
let previousUrl = window.location.href;
const urlChangeDetector = setInterval(() => {
  if (window.location.href !== previousUrl) {
    previousUrl = window.location.href;
    console.log('URL changed, reinitializing Sponsor Sniper');
    hasSetupSkipListener = false; // Reset listener state
    initialize();
  }
}, 1000); 