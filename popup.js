// Popup script for Sponsor Sniper extension

document.addEventListener('DOMContentLoaded', function() {
  // Get UI elements
  const enableSkippingToggle = document.getElementById('enable-skipping');
  const showNotificationsToggle = document.getElementById('show-notifications');
  const debugModeToggle = document.getElementById('debug-mode');
  const connectionStatus = document.getElementById('connection-status');
  
  // Check backend connection using background script
  checkBackendConnection();
  
  // Load saved settings from Chrome storage
  chrome.storage.sync.get(
    {
      enableSkipping: true,
      showNotifications: true,
      debugMode: true
    },
    function(items) {
      enableSkippingToggle.checked = items.enableSkipping;
      showNotificationsToggle.checked = items.showNotifications;
      debugModeToggle.checked = items.debugMode;
    }
  );
  
  // Save settings when toggle is changed
  enableSkippingToggle.addEventListener('change', function() {
    chrome.storage.sync.set(
      { enableSkipping: enableSkippingToggle.checked },
      function() {
        console.log('Enable skipping setting saved:', enableSkippingToggle.checked);
      }
    );
  });
  
  showNotificationsToggle.addEventListener('change', function() {
    chrome.storage.sync.set(
      { showNotifications: showNotificationsToggle.checked },
      function() {
        console.log('Show notifications setting saved:', showNotificationsToggle.checked);
      }
    );
  });
  
  debugModeToggle.addEventListener('change', function() {
    chrome.storage.sync.set(
      { debugMode: debugModeToggle.checked },
      function() {
        console.log('Debug mode setting saved:', debugModeToggle.checked);
      }
    );
  });
  
  // Function to check backend connection via background script
  function checkBackendConnection() {
    connectionStatus.textContent = 'Checking backend connection...';
    connectionStatus.style.color = '#2196F3';
    
    // Use background script for ping
    chrome.runtime.sendMessage({ type: 'pingBackend' }, response => {
      console.log('Ping response:', response);
      
      if (response && response.success && response.data && response.data.status === 'ok') {
        connectionStatus.textContent = 'Backend connection: OK';
        connectionStatus.style.color = 'green';
      } else {
        // If background script fails, try direct fetch
        console.log('Background ping failed, trying direct ping');
        directPing();
      }
    });
  }
  
  // Direct ping function as fallback
  function directPing() {
    fetch('http://localhost:8080/ping')
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Failed to connect to backend');
      })
      .then(data => {
        if (data.status === 'ok') {
          connectionStatus.textContent = 'Backend connection: OK';
          connectionStatus.style.color = 'green';
        } else {
          throw new Error('Unexpected backend response');
        }
      })
      .catch(error => {
        console.error('Error connecting to backend:', error);
        connectionStatus.textContent = 'Backend connection: FAILED';
        connectionStatus.style.color = 'red';
      });
  }
}); 