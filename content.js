// Content script for Sponsor Sniper extension
// This script runs on YouTube pages and handles the sponsor skipping functionality

console.log('Sponsor Sniper initialized');

// Default settings
let settings = {
  enableSkipping: true,
  showNotifications: true
};

// Load settings from storage
function loadSettings() {
  chrome.storage.sync.get(
    {
      enableSkipping: true,
      showNotifications: true
    },
    function(items) {
      settings = items;
      console.log('Settings loaded:', settings);
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
  try {
    // Connect to our backend API to get sponsor segments
    const response = await fetch(`http://localhost:8080/sponsors?v=${videoId}&threshold=0.3`);
    if (!response.ok) {
      throw new Error('Failed to fetch sponsor segments');
    }
    const data = await response.json();
    
    // Check if the API call was successful
    if (!data.success) {
      throw new Error(data.error || 'API error occurred');
    }
    
    return data.sponsors || [];
  } catch (error) {
    console.error('Error fetching sponsor segments:', error);
    return [];
  }
}

// Function to show notification when skipping a sponsor
function showSkipNotification() {
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
    `;
    document.body.appendChild(notification);
  }
  
  // Set notification text and show it
  notification.textContent = 'Sponsor skipped';
  notification.style.opacity = '1';
  
  // Hide notification after 2 seconds
  setTimeout(() => {
    notification.style.opacity = '0';
  }, 2000);
}

// Function to skip to a specific time in the video
function skipToTime(seconds) {
  const videoElement = document.querySelector('video');
  if (videoElement) {
    videoElement.currentTime = seconds;
    console.log(`Skipped to ${seconds} seconds`);
    showSkipNotification();
  }
}

// Function to monitor video playback and skip sponsor segments
function monitorAndSkipSponsors(sponsorSegments) {
  if (!sponsorSegments || sponsorSegments.length === 0) return;
  
  const videoElement = document.querySelector('video');
  if (!videoElement) return;
  
  // Listen for time updates on the video element
  videoElement.addEventListener('timeupdate', () => {
    // Check if skipping is enabled in settings
    if (!settings.enableSkipping) return;
    
    const currentTime = videoElement.currentTime;
    
    // Check if current time is within any sponsor segment
    for (const segment of sponsorSegments) {
      if (currentTime >= segment.startTime && currentTime < segment.endTime) {
        // Skip to the end of the sponsor segment
        skipToTime(segment.endTime);
        break;
      }
    }
  });
}

// Main initialization function
async function initialize() {
  // Load settings first
  loadSettings();
  
  // Only run on YouTube watch pages
  if (!isYouTubeWatchPage()) return;
  
  // Get the video ID
  const videoId = getVideoId();
  if (!videoId) {
    console.error('Could not determine video ID');
    return;
  }
  
  console.log(`Processing YouTube video: ${videoId}`);
  
  // Wait for the video element to be ready
  let attempts = 0;
  const checkVideoElement = setInterval(async () => {
    const videoElement = document.querySelector('video');
    attempts++;
    
    if (videoElement) {
      clearInterval(checkVideoElement);
      
      // Fetch sponsor segments from the backend
      const sponsorSegments = await getSponsorSegments(videoId);
      
      // Start monitoring and skipping sponsors
      monitorAndSkipSponsors(sponsorSegments);
    } else if (attempts >= 10) {
      // Give up after 10 attempts (5 seconds)
      clearInterval(checkVideoElement);
      console.error('Video element not found after multiple attempts');
    }
  }, 500);
}

// Run the extension on page load
initialize();

// Re-run the extension when navigating between YouTube videos (SPA navigation)
let previousUrl = window.location.href;
const urlChangeDetector = setInterval(() => {
  if (window.location.href !== previousUrl) {
    previousUrl = window.location.href;
    console.log('URL changed, reinitializing Sponsor Sniper');
    initialize();
  }
}, 1000); 