// Popup script for Sponsor Sniper extension

document.addEventListener('DOMContentLoaded', function() {
  // Get UI elements
  const enableSkippingToggle = document.getElementById('enable-skipping');
  const showNotificationsToggle = document.getElementById('show-notifications');
  
  // Load saved settings from Chrome storage
  chrome.storage.sync.get(
    {
      enableSkipping: true,
      showNotifications: true
    },
    function(items) {
      enableSkippingToggle.checked = items.enableSkipping;
      showNotificationsToggle.checked = items.showNotifications;
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
}); 