// Content script - runs in the context of web pages
// Syncs Firebase credentials from web app localStorage to extension

console.log('[DAN Content] Content script loaded on:', window.location.hostname);

// Sync credentials from localStorage to extension storage
async function syncCredentialsFromWebApp() {
  try {
    const configStr = localStorage.getItem('dan_extension_config');
    const userId = localStorage.getItem('dan_extension_userId');
    const authToken = localStorage.getItem('dan_extension_authToken');

    console.log('[DAN Content] Checking localStorage:', {
      hasConfig: !!configStr,
      hasUserId: !!userId,
      hasAuthToken: !!authToken,
    });

    if (configStr && userId) {
      const firebaseConfig = JSON.parse(configStr);
      
      console.log('[DAN Content] 📤 Sending SYNC_CREDENTIALS to background...');
      
      // Send to background script to store with error handling
      chrome.runtime.sendMessage({
        type: 'SYNC_CREDENTIALS',
        firebaseConfig,
        userId,
        authToken: authToken || null,
      }, (response) => {
        // Check for errors
        if (chrome.runtime.lastError) {
          console.log('[DAN Content] Background script not ready:', chrome.runtime.lastError.message);
          setTimeout(syncCredentialsFromWebApp, 1000);
          return;
        }
        
        if (response?.success) {
          console.log('[DAN Content] ✅ Credentials synced to extension storage');
        }
      });
    } else {
      console.log('[DAN Content] ⚠️ No credentials found in localStorage (user not logged in?)');
    }
  } catch (error) {
    console.error('[DAN Content] Error syncing credentials:', error);
  }
}

// Sync with retry logic (background script might not be ready immediately)
function syncWithRetry(retries = 3) {
  syncCredentialsFromWebApp();
  
  // Retry a few times if background script isn't ready
  if (retries > 0) {
    setTimeout(() => syncWithRetry(retries - 1), 2000);
  }
}

// Start syncing (with retries)
syncWithRetry();

// Also sync when localStorage changes (user logs in/out)
// Use a more reliable method than overriding setItem
let lastConfig = localStorage.getItem('dan_extension_config');
let lastUserId = localStorage.getItem('dan_extension_userId');
let lastAuthToken = localStorage.getItem('dan_extension_authToken');

// Poll for localStorage changes (more reliable than overriding setItem)
setInterval(() => {
  const currentConfig = localStorage.getItem('dan_extension_config');
  const currentUserId = localStorage.getItem('dan_extension_userId');
  const currentAuthToken = localStorage.getItem('dan_extension_authToken');
  
  if (currentConfig !== lastConfig || currentUserId !== lastUserId || currentAuthToken !== lastAuthToken) {
    lastConfig = currentConfig;
    lastUserId = currentUserId;
    lastAuthToken = currentAuthToken;
    syncCredentialsFromWebApp();
  }
}, 1000);

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'EXTRACT_CONTENT') {
    // Extract main content for AI summary
    const content = extractMainContent();
    sendResponse({ content });
  }
  return true;
});

function extractMainContent(): string {
  // Simple content extraction - can be enhanced
  const title = document.title;
  const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
    .map(h => h.textContent)
    .filter(Boolean)
    .join(' | ');
  
  return `${title} - ${headings}`;
}

