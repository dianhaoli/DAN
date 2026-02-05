import { 
  STUDY_DOMAINS, 
  DISTRACTION_DOMAINS, 
  MIN_SESSION_DURATION_SECONDS,
  extractDomain,
  isStudyDomain,
  calculateFocusScore,
  calculateXP
} from '@dan/shared';
import { BACKEND_URL } from '../config';

interface SessionData {
  startTime: number;
  domains: Set<string>;
  tabSwitches: number;
  activeTime: number;
  idleTime: number;
  lastActivityTime: number;
  topic: string;
  isActive: boolean;
  source: 'extension' | 'manual';
}

export class SessionTracker {
  private currentSession: SessionData | null = null;
  private lastDomain: string = '';

  constructor() {
    this.loadSession();
  }

  private async loadSession() {
    const stored = await chrome.storage.local.get('currentSession');
    if (stored.currentSession) {
      this.currentSession = {
        ...stored.currentSession,
        domains: new Set(stored.currentSession.domains),
      };
    }
  }

  private async saveSession() {
    if (this.currentSession) {
      await chrome.storage.local.set({
        currentSession: {
          ...this.currentSession,
          domains: Array.from(this.currentSession.domains),
        },
      });
    }
  }

  handleTabChange(url: string, title: string) {
    const domain = extractDomain(url);
    if (!domain) return;

    // Check if it's a distraction domain
    if (isStudyDomain(domain, DISTRACTION_DOMAINS)) {
      this.stopSession();
      return;
    }

    // Check if it's a study domain
    if (isStudyDomain(domain, STUDY_DOMAINS)) {
      if (!this.currentSession) {
        this.startSession(domain, title);
      } else {
        this.updateSession(domain);
      }
    }
  }

  private startSession(domain: string, title: string) {
    const now = Date.now();
    this.currentSession = {
      startTime: now,
      domains: new Set([domain]),
      tabSwitches: 0,
      activeTime: 0,
      idleTime: 0,
      lastActivityTime: now,
      topic: title,
      isActive: true,
      source: 'extension',
    };
    this.lastDomain = domain;
    this.saveSession();
    this.notifySessionStart();
  }

  startManualSession(topic: string) {
    const now = Date.now();
    this.currentSession = {
      startTime: now,
      domains: new Set(),
      tabSwitches: 0,
      activeTime: 0,
      idleTime: 0,
      lastActivityTime: now,
      topic: topic,
      isActive: true,
      source: 'manual',
    };
    this.saveSession();
    this.notifySessionStart();
  }

  private updateSession(domain: string) {
    if (!this.currentSession) return;

    if (domain !== this.lastDomain) {
      this.currentSession.tabSwitches++;
      this.lastDomain = domain;
    }

    this.currentSession.domains.add(domain);
    this.saveSession();
  }

  updateCurrentSession() {
    if (!this.currentSession || !this.currentSession.isActive) return;

    const now = Date.now();
    const timeSinceLastActivity = (now - this.currentSession.lastActivityTime) / 1000;

    // Add to active time (capped at tracking interval)
    this.currentSession.activeTime += Math.min(timeSinceLastActivity, 30);
    this.currentSession.lastActivityTime = now;

    this.saveSession();
  }

  handleIdle() {
    if (!this.currentSession) return;

    this.currentSession.isActive = false;
    const now = Date.now();
    const timeSinceLastActivity = (now - this.currentSession.lastActivityTime) / 1000;
    this.currentSession.idleTime += timeSinceLastActivity;

    this.saveSession();
  }

  handleActive() {
    if (!this.currentSession) return;

    this.currentSession.isActive = true;
    this.currentSession.lastActivityTime = Date.now();
    this.saveSession();
  }

  async stopSession() {
    if (!this.currentSession) {
      console.log('[SessionTracker] No active session to stop');
      return;
    }

    const now = Date.now();
    const duration = (now - this.currentSession.startTime) / 1000;

    console.log('[SessionTracker] 🛑 Stopping session:', {
      duration: Math.round(duration),
      minRequired: MIN_SESSION_DURATION_SECONDS,
      topic: this.currentSession.topic,
    });

    // Only save sessions longer than minimum duration
    if (duration >= MIN_SESSION_DURATION_SECONDS) {
      console.log('[SessionTracker] ✅ Duration meets minimum, will save session');
      try {
        await this.saveSessionToBackend();
      } catch (error) {
        console.error('[SessionTracker] ❌ Error saving session:', error);
      }
    } else {
      console.log('[SessionTracker] ⏱️ Session too short, not saving (need at least', MIN_SESSION_DURATION_SECONDS, 'seconds)');
    }

    // Always clear the session
    this.currentSession = null;
    await chrome.storage.local.remove('currentSession');
    this.notifySessionEnd();
    
    console.log('[SessionTracker] ✅ Session stopped and cleared');
  }

  private async saveSessionToBackend() {
    if (!this.currentSession) return;

    const now = Date.now();
    const duration = (now - this.currentSession.startTime) / 1000;
    const totalTime = this.currentSession.activeTime + this.currentSession.idleTime;

    console.log('[SessionTracker] 🔄 Starting save process:', {
      duration: Math.round(duration),
      topic: this.currentSession.topic,
      domains: Array.from(this.currentSession.domains),
    });

    // Calculate focus score
    const focusScore = calculateFocusScore(
      this.currentSession.activeTime,
      Math.max(totalTime, duration),
      this.currentSession.tabSwitches
    );

    // Calculate XP
    const durationMinutes = duration / 60;
    const xpEarned = calculateXP(durationMinutes, focusScore);

    // Get stored credentials
    const { userId, authToken } = await chrome.storage.local.get(['userId', 'authToken']);
    
    console.log('[SessionTracker] Credentials check:', {
      hasUserId: !!userId,
      hasAuthToken: !!authToken,
      userIdPreview: userId ? userId.substring(0, 8) + '...' : 'none',
    });
    
    if (!userId) {
      console.error('[SessionTracker] ❌ No user ID found. User must log in via web app first.');
      // Store for retry later
      await this.storeForRetry({
        startTime: this.currentSession.startTime,
        endTime: now,
        duration: Math.round(duration),
        topic: this.currentSession.topic,
        domains: Array.from(this.currentSession.domains),
        focusScore,
        tabSwitches: this.currentSession.tabSwitches,
        activeTime: Math.round(this.currentSession.activeTime),
        idleTime: Math.round(this.currentSession.idleTime),
        xpEarned,
        source: this.currentSession.source,
      });
      return;
    }

    // Prepare session data for FastAPI
    const sessionData = {
      start_time: new Date(this.currentSession.startTime).toISOString(),
      end_time: new Date(now).toISOString(),
      duration: Math.round(duration),
      topic: this.currentSession.topic,
      domains: Array.from(this.currentSession.domains),
      title: this.currentSession.topic,
      tab_switches: this.currentSession.tabSwitches,
      active_time: Math.round(this.currentSession.activeTime),
      idle_time: Math.round(this.currentSession.idleTime),
      clicks: 0,
      keystrokes: 0,
      source: this.currentSession.source,
      platform: 'chrome-extension',
    };

    if (!authToken) {
      console.error('[SessionTracker] ❌ No auth token found. User must log in via web app first.');
      console.log('[SessionTracker] 💡 Open localhost:3000 and make sure you are logged in.');
      await this.storeForRetry(sessionData);
      return;
    }

    // Save via FastAPI backend
    try {
      console.log('[SessionTracker] 📤 POSTing to FastAPI backend:', BACKEND_URL + '/sessions');
      const response = await fetch(`${BACKEND_URL}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify(sessionData),
      });

      console.log('[SessionTracker] Response status:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('[SessionTracker] ✅ Session saved successfully!', {
          sessionId: result.id || result.sessionId,
          userId,
          duration: Math.round(duration),
          topic: this.currentSession.topic,
        });
        
        await chrome.storage.local.remove('pendingSessions');
        return;
      } else {
        const errorText = await response.text();
        console.error('[SessionTracker] ❌ FastAPI backend error:', {
          status: response.status,
          error: errorText,
        });
        
        // If token is expired (401), mark it for refresh
        if (response.status === 401) {
          console.error('[SessionTracker] 🔑 Auth token may be expired. Open web app to refresh.');
        }
        
        await this.storeForRetry(sessionData);
      }
    } catch (error) {
      console.error('[SessionTracker] ❌ Network error saving session:', error);
      await this.storeForRetry(sessionData);
    }
  }

  private async storeForRetry(sessionData: any) {
    const { pendingSessions = [] } = await chrome.storage.local.get('pendingSessions');
    pendingSessions.push(sessionData);
    await chrome.storage.local.set({ pendingSessions });
  }

  private notifySessionStart() {
    chrome.runtime.sendMessage({ type: 'SESSION_STARTED' }, (response) => {
      // Ignore errors - it's okay if no listeners are present
      if (chrome.runtime.lastError) {
        // Popup might not be open, that's fine
      }
    });
  }

  private notifySessionEnd() {
    chrome.runtime.sendMessage({ type: 'SESSION_ENDED' }, (response) => {
      // Ignore errors - it's okay if no listeners are present
      if (chrome.runtime.lastError) {
        // Popup might not be open, that's fine
      }
    });
  }

  getSessionStatus() {
    if (!this.currentSession) {
      return { active: false };
    }

    const now = Date.now();
    const duration = (now - this.currentSession.startTime) / 1000;

    return {
      active: true,
      topic: this.currentSession.topic,
      duration: Math.round(duration),
      domains: Array.from(this.currentSession.domains),
      tabSwitches: this.currentSession.tabSwitches,
      isActive: this.currentSession.isActive,
    };
  }
}

