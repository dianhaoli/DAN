// Popup script
document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('status');
  const topicEl = document.getElementById('topic');
  const durationEl = document.getElementById('duration');
  const startBtn = document.getElementById('startBtn') as HTMLButtonElement;
  const stopBtn = document.getElementById('stopBtn') as HTMLButtonElement;
  const manualTopicInput = document.getElementById('manualTopic') as HTMLInputElement;

  let updateInterval: number | null = null;

  // Get session status
  function updateStatus() {
    chrome.runtime.sendMessage({ type: 'GET_SESSION_STATUS' }, (response) => {
      if (chrome.runtime.lastError) {
        // Background script might not be ready yet, that's okay
        console.log('Background script not ready:', chrome.runtime.lastError.message);
        return;
      }
      
      if (!response) return;
      
      if (response.active) {
        statusEl!.textContent = response.isActive ? 'Active' : 'Idle';
        statusEl!.className = response.isActive ? 'status-active' : 'status-idle';
        topicEl!.textContent = response.topic;
        durationEl!.textContent = formatDuration(response.duration);
        
        startBtn!.style.display = 'none';
        stopBtn!.style.display = 'block';
        manualTopicInput!.disabled = true;
      } else {
        statusEl!.textContent = 'No active session';
        statusEl!.className = 'status-inactive';
        topicEl!.textContent = '-';
        durationEl!.textContent = '0:00';
        
        startBtn!.style.display = 'block';
        stopBtn!.style.display = 'none';
        manualTopicInput!.disabled = false;
      }
    });
  }

  // Start manual session
  startBtn?.addEventListener('click', () => {
    const topic = manualTopicInput!.value.trim() || 'Study Session';
    chrome.runtime.sendMessage({ 
      type: 'START_MANUAL_SESSION',
      topic 
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Error starting session:', chrome.runtime.lastError.message);
        alert('Failed to start session. Please try again.');
        return;
      }
      manualTopicInput!.value = '';
      updateStatus();
    });
  });

  // Stop session
  stopBtn?.addEventListener('click', async () => {
    if (!stopBtn) {
      console.error('[Popup] Stop button not found');
      return;
    }
    
    console.log('[Popup] Stop button clicked');
    
    // Disable button while processing
    stopBtn.disabled = true;
    const originalText = stopBtn.textContent;
    stopBtn.textContent = 'Stopping...';
    
    try {
      console.log('[Popup] Sending STOP_SESSION message to background');
      
      const response = await new Promise<any>((resolve, reject) => {
        chrome.runtime.sendMessage({ type: 'STOP_SESSION' }, (response) => {
          if (chrome.runtime.lastError) {
            console.error('[Popup] Chrome runtime error:', chrome.runtime.lastError.message);
            reject(new Error(chrome.runtime.lastError.message));
            return;
          }
          console.log('[Popup] Received response from background:', response);
          resolve(response);
        });
      });

      console.log('[Popup] Response received:', response);

      if (response?.error) {
        console.error('[Popup] Error stopping session:', response.error);
        alert(`Failed to stop session: ${response.error}`);
      } else if (response?.success) {
        console.log('[Popup] ✅ Session stopped successfully');
      } else {
        console.warn('[Popup] Unexpected response format:', response);
      }
      
      // Update UI regardless of success/failure
      console.log('[Popup] Updating status after stop');
      updateStatus();
    } catch (error) {
      console.error('[Popup] Exception stopping session:', error);
      alert(`Failed to stop session: ${error instanceof Error ? error.message : 'Unknown error'}`);
      updateStatus(); // Still update to reflect current state
    } finally {
      // Re-enable button
      if (stopBtn) {
        stopBtn.disabled = false;
        stopBtn.textContent = originalText || 'Stop Session';
      }
    }
  });

  // Open dashboard
  document.getElementById('dashboardBtn')?.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });

  // Debug info
  function showDebugInfo() {
    chrome.runtime.sendMessage({ type: 'GET_DEBUG_INFO' }, (debugInfo) => {
      if (chrome.runtime.lastError) {
        // Background script might not be ready yet, that's okay
        console.log('Background script not ready:', chrome.runtime.lastError.message);
        const debugEl = document.getElementById('debugInfo');
        if (debugEl) {
          debugEl.innerHTML = `
            <div style="font-size: 11px; color: #999; margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
              <div>⏳ Loading...</div>
            </div>
          `;
        }
        return;
      }
      
      if (!debugInfo) {
        const debugEl = document.getElementById('debugInfo');
        if (debugEl) {
          debugEl.innerHTML = `
            <div style="font-size: 11px; color: #999; margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
              <div>⏳ Loading...</div>
            </div>
          `;
        }
        return;
      }
      
      console.log('Extension Debug Info:', debugInfo);
      
      // Show in popup if there's a debug section
      const debugEl = document.getElementById('debugInfo');
      if (debugEl) {
        const allConfigured = debugInfo.hasFirebaseConfig && debugInfo.hasUserId && debugInfo.hasAuthToken;
        debugEl.innerHTML = `
          <div style="font-size: 11px; color: #666; margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px;">
            <div><strong>Firebase:</strong> ${debugInfo.hasFirebaseConfig ? '✅ Configured' : '❌ Not configured'}</div>
            <div><strong>User ID:</strong> ${debugInfo.hasUserId ? '✅ ' + (debugInfo.userId?.substring(0, 8) + '...') : '❌ Missing'}</div>
            <div><strong>Auth Token:</strong> ${debugInfo.hasAuthToken ? '✅ Present' : '❌ Missing (login to web app)'}</div>
            <div><strong>Pending Sessions:</strong> ${debugInfo.pendingSessionsCount}</div>
            ${debugInfo.currentSession?.active ? `<div><strong>Active Session:</strong> ${debugInfo.currentSession.duration}s</div>` : ''}
            ${!allConfigured ? `<div style="color: #e53935; margin-top: 5px;">⚠️ Open web app and login to sync</div>` : ''}
          </div>
        `;
      }
    });
  }

  // Test save button (for debugging)
  const testBtn = document.createElement('button');
  testBtn.textContent = 'Test Save Session';
  testBtn.className = 'btn btn-secondary';
  testBtn.style.marginTop = '10px';
  testBtn.style.fontSize = '11px';
  testBtn.addEventListener('click', () => {
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';
    
    // Add timeout in case background script doesn't respond
    const timeoutId = setTimeout(() => {
      testBtn.disabled = false;
      testBtn.textContent = 'Test Save Session';
      alert('❌ Background script not responding.\n\n💡 Try:\n1. Go to chrome://extensions\n2. Click the reload button on DAN extension\n3. Open the web app (localhost:3000) while logged in\n4. Try again');
    }, 10000); // 10 second timeout
    
    chrome.runtime.sendMessage({ type: 'TEST_SAVE_SESSION' }, (result) => {
      clearTimeout(timeoutId);
      testBtn.disabled = false;
      testBtn.textContent = 'Test Save Session';
      
      if (chrome.runtime.lastError) {
        alert(`❌ Error: ${chrome.runtime.lastError.message}\n\n💡 Try reloading the extension at chrome://extensions`);
        return;
      }
      
      if (result?.success) {
        alert(`✅ Test session saved! ID: ${result.sessionId}\n\nCheck your Sessions page in the web app.`);
      } else {
        alert(`❌ Failed: ${result?.error || 'Unknown error'}\n\n💡 Tips:\n- Make sure the web app (localhost:3000) is open\n- Make sure you're logged in\n- Try refreshing the web app page`);
      }
    });
  });
  
  // Refresh credentials button
  const refreshBtn = document.createElement('button');
  refreshBtn.textContent = 'Sync Credentials';
  refreshBtn.className = 'btn btn-secondary';
  refreshBtn.style.marginTop = '5px';
  refreshBtn.style.fontSize = '11px';
  refreshBtn.addEventListener('click', () => {
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Syncing...';
    // Open web app to trigger credential sync
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' }, () => {
      setTimeout(() => {
        refreshBtn.disabled = false;
        refreshBtn.textContent = 'Sync Credentials';
        showDebugInfo(); // Refresh debug info
      }, 2000);
    });
  });

  // Add debug section to popup
  const actionsDiv = document.querySelector('.actions');
  if (actionsDiv) {
    const debugDiv = document.createElement('div');
    debugDiv.id = 'debugInfo';
    debugDiv.style.marginTop = '10px';
    actionsDiv.appendChild(debugDiv);
    actionsDiv.appendChild(testBtn);
    actionsDiv.appendChild(refreshBtn);
  }

  // Initial update
  updateStatus();
  showDebugInfo();

  // Update every second
  updateInterval = window.setInterval(() => {
    updateStatus();
    showDebugInfo();
  }, 1000);

  // Listen for session changes
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'SESSION_STARTED' || message.type === 'SESSION_ENDED') {
      updateStatus();
      showDebugInfo();
    }
  });
});

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

