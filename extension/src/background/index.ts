import { STUDY_DOMAINS, DISTRACTION_DOMAINS, IDLE_THRESHOLD_SECONDS, TRACKING_INTERVAL_SECONDS } from '@dan/shared';
import { SessionTracker } from './sessionTracker';

console.log('DAN Extension: Background service worker initialized');

const sessionTracker = new SessionTracker();

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

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_SESSION_STATUS') {
    sendResponse(sessionTracker.getSessionStatus());
  } else if (message.type === 'START_MANUAL_SESSION') {
    sessionTracker.startManualSession(message.topic);
    sendResponse({ success: true });
  } else if (message.type === 'STOP_SESSION') {
    sessionTracker.stopSession();
    sendResponse({ success: true });
  }
  return true; // Keep message channel open for async response
});

// Check for study domains on startup
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]?.url) {
    sessionTracker.handleTabChange(tabs[0].url, tabs[0].title || '');
  }
});

