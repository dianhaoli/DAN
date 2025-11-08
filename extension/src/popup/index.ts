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
  async function updateStatus() {
    const response = await chrome.runtime.sendMessage({ type: 'GET_SESSION_STATUS' });
    
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
  }

  // Start manual session
  startBtn?.addEventListener('click', async () => {
    const topic = manualTopicInput!.value.trim() || 'Study Session';
    await chrome.runtime.sendMessage({ 
      type: 'START_MANUAL_SESSION',
      topic 
    });
    manualTopicInput!.value = '';
    updateStatus();
  });

  // Stop session
  stopBtn?.addEventListener('click', async () => {
    await chrome.runtime.sendMessage({ type: 'STOP_SESSION' });
    updateStatus();
  });

  // Open dashboard
  document.getElementById('dashboardBtn')?.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });

  // Initial update
  updateStatus();

  // Update every second
  updateInterval = window.setInterval(updateStatus, 1000);

  // Listen for session changes
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'SESSION_STARTED' || message.type === 'SESSION_ENDED') {
      updateStatus();
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

