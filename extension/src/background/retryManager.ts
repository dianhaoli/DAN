import { getCurrentUserId } from '../lib/firebase';

interface PendingSession {
  startTime: number;
  endTime: number;
  duration: number;
  topic: string;
  domains: string[];
  focusScore: number;
  tabSwitches: number;
  activeTime: number;
  idleTime: number;
  xpEarned: number;
  source: 'extension' | 'manual';
}

export class RetryManager {
  private static RETRY_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
  private static MAX_RETRIES = 10;

  static async retryPendingSessions() {
    const { pendingSessions = [] } = await chrome.storage.local.get('pendingSessions');
    
    if (pendingSessions.length === 0) return;

    console.log(`[RetryManager] Retrying ${pendingSessions.length} pending sessions...`);

    const userId = await getCurrentUserId();
    if (!userId) {
      console.log('[RetryManager] No user ID available. Will retry later.');
      return;
    }

    // Get auth token for backend API
    const { authToken } = await chrome.storage.local.get('authToken');
    if (!authToken) {
      console.log('[RetryManager] No auth token available. Will retry later.');
      return;
    }

    const { BACKEND_URL } = await import('../config');
    const successful: number[] = [];
    const failed: PendingSession[] = [];

    for (let i = 0; i < pendingSessions.length; i++) {
      const session = pendingSessions[i] as PendingSession;
      
      try {
        // Use the same format as regular session saves (SessionCreate schema)
        const sessionData = {
          start_time: new Date(session.startTime).toISOString(),
          end_time: new Date(session.endTime).toISOString(),
          duration: session.duration,
          topic: session.topic,
          domains: session.domains,
          title: session.topic,
          tab_switches: session.tabSwitches,
          active_time: session.activeTime,
          idle_time: session.idleTime,
          clicks: 0,
          keystrokes: 0,
          source: session.source,
          platform: 'chrome-extension',
        };

        const response = await fetch(`${BACKEND_URL}/sessions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify(sessionData),
        });

        if (response.ok) {
          const result = await response.json();
          successful.push(i);
          console.log(`[RetryManager] ✅ Successfully saved pending session: ${session.topic}`, {
            sessionId: result.id,
          });
        } else {
          const errorText = await response.text();
          console.error(`[RetryManager] ❌ Failed to save pending session ${i}:`, response.status, errorText);
          failed.push(session);
        }
      } catch (error) {
        console.error(`[RetryManager] ❌ Exception saving pending session ${i}:`, error);
        failed.push(session);
      }
    }

    // Update storage with only failed sessions
    if (failed.length > 0) {
      await chrome.storage.local.set({ pendingSessions: failed });
      console.log(`[RetryManager] ${failed.length} sessions still pending, will retry later`);
    } else {
      await chrome.storage.local.remove('pendingSessions');
      console.log(`[RetryManager] ✅ All pending sessions saved successfully`);
    }

    if (successful.length > 0) {
      console.log(`[RetryManager] ✅ Successfully retried ${successful.length} sessions`);
    }
  }

  static startRetryLoop() {
    // Retry immediately
    this.retryPendingSessions();
    
    // Then retry every 5 minutes
    setInterval(() => {
      this.retryPendingSessions();
    }, this.RETRY_INTERVAL_MS);
  }
}

