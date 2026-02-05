import { STUDY_DOMAINS, DISTRACTION_DOMAINS, IDLE_THRESHOLD_SECONDS, TRACKING_INTERVAL_SECONDS } from '@dan/shared';
import { SessionTracker } from './sessionTracker';
import { RetryManager } from './retryManager';
import { BACKEND_URL } from '../config';

console.log('[Background] DAN Extension: Background service worker initialized');
console.log('[Background] Backend URL:', BACKEND_URL);

const sessionTracker = new SessionTracker();

// Start retry manager for pending sessions
RetryManager.startRetryLoop();

// Track active tab changes
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  if (tab.url) {
    sessionTracker.handleTabChange(tab.url, tab.title || '');
  }
});

// Track tab updates (URL changes)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url && tab.active) {
    sessionTracker.handleTabChange(changeInfo.url, tab.title || '');
  }
});

// Track idle state changes
chrome.idle.onStateChanged.addListener((newState) => {
  if (newState === 'idle' || newState === 'locked') {
    sessionTracker.handleIdle();
  } else if (newState === 'active') {
    sessionTracker.handleActive();
  }
});

// Set idle detection interval
chrome.idle.setDetectionInterval(IDLE_THRESHOLD_SECONDS);

// Periodic session update
setInterval(() => {
  sessionTracker.updateCurrentSession();
}, TRACKING_INTERVAL_SECONDS * 1000);

// Listen for messages from popup and web app
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Handle async responses properly
  const handleMessage = async () => {
    try {
      if (message.type === 'GET_SESSION_STATUS') {
        return sessionTracker.getSessionStatus();
      } else if (message.type === 'START_MANUAL_SESSION') {
        sessionTracker.startManualSession(message.topic);
        return { success: true };
      } else if (message.type === 'STOP_SESSION') {
        console.log('[Background] Received STOP_SESSION message');
        try {
          await sessionTracker.stopSession();
          console.log('[Background] ✅ Session stopped successfully');
          return { success: true };
        } catch (error) {
          console.error('[Background] ❌ Error stopping session:', error);
          return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
        }
      } else if (message.type === 'SYNC_CREDENTIALS') {
        // Store Firebase config, user ID, and auth token from web app
        await chrome.storage.local.set({
          firebaseConfig: message.firebaseConfig,
          userId: message.userId,
          authToken: message.authToken || null,
        });
        console.log('[Background] ✅ Credentials synced from web app');
        console.log('[Background] User ID:', message.userId);
        console.log('[Background] Firebase config present:', !!message.firebaseConfig?.apiKey);
        console.log('[Background] Auth token present:', !!message.authToken);
        return { success: true };
      } else if (message.type === 'PING') {
        return { pong: true };
      } else if (message.type === 'GET_DEBUG_INFO') {
        // Return debug information
        const { firebaseConfig, userId, pendingSessions, authToken } = await chrome.storage.local.get([
          'firebaseConfig',
          'userId',
          'pendingSessions',
          'authToken',
        ]);
        const sessionStatus = sessionTracker.getSessionStatus();
        return {
          hasFirebaseConfig: !!firebaseConfig?.apiKey,
          hasUserId: !!userId,
          hasAuthToken: !!authToken,
          userId: userId || null,
          pendingSessionsCount: pendingSessions?.length || 0,
          currentSession: sessionStatus,
        };
      } else if (message.type === 'TEST_SAVE_SESSION') {
        // Test function to manually save a session
        console.log('[Background] 🧪 TEST_SAVE_SESSION triggered');
        
        // Check stored credentials
        const { userId, authToken } = await chrome.storage.local.get(['userId', 'authToken']);
        
        console.log('[Background] Stored credentials:', {
          hasUserId: !!userId,
          hasAuthToken: !!authToken,
        });
        
        if (!userId) {
          console.error('[Background] ❌ No userId in chrome.storage.local');
          return { 
            success: false, 
            error: 'User ID not found. Open the web app (localhost:3000), login, and make sure you are on a page.' 
          };
        }

        if (!authToken) {
          console.error('[Background] ❌ No authToken in chrome.storage.local');
          return { 
            success: false, 
            error: 'Auth token not found. Open the web app (localhost:3000) and refresh the page while logged in.' 
          };
        }

        const now = Date.now();
        
        const testSession = {
          start_time: new Date(now - 120000).toISOString(),
          end_time: new Date(now).toISOString(),
          duration: 120,
          topic: 'Test Session',
          domains: ['test.com'],
          title: 'Test Session',
          tab_switches: 2,
          active_time: 110,
          idle_time: 10,
          clicks: 0,
          keystrokes: 0,
          source: 'manual',
          platform: 'chrome-extension',
        };

        try {
          console.log('[Background] 📤 POSTing test session to:', BACKEND_URL + '/sessions');
          const response = await fetch(`${BACKEND_URL}/sessions`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify(testSession),
          });

          console.log('[Background] Response status:', response.status);

          if (response.ok) {
            const result = await response.json();
            console.log('[Background] ✅ Test session saved!', result);
            return { success: true, sessionId: result.id || result.sessionId };
          } else {
            const errorText = await response.text();
            console.error('[Background] ❌ Test failed:', response.status, errorText);
            
            if (response.status === 401) {
              return { 
                success: false, 
                error: `Auth token expired or invalid. Refresh the web app page to get a new token.` 
              };
            }
            
            return { 
              success: false, 
              error: `Backend returned ${response.status}: ${errorText}` 
            };
          }
        } catch (error) {
          console.error('[Background] ❌ Network error:', error);
          return { 
            success: false, 
            error: error instanceof Error ? error.message : 'Failed to connect to backend (is it running?)' 
          };
        }
      }
      return { error: 'Unknown message type' };
    } catch (error) {
      console.error('Error handling message:', error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  };

  // Handle async response
  handleMessage().then(response => {
    sendResponse(response);
  }).catch(error => {
    sendResponse({ error: error.message });
  });

  return true; // Keep message channel open for async response
});

// Check for study domains on startup
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]?.url) {
    sessionTracker.handleTabChange(tabs[0].url, tabs[0].title || '');
  }
});

