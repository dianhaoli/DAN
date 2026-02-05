import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, onAuthStateChanged, signInWithCustomToken } from 'firebase/auth';
import { getFirestore, Timestamp, connectFirestoreEmulator } from 'firebase/firestore';

// Firebase config - gets from chrome.storage (synced from web app)
const getFirebaseConfig = async () => {
  // Get config from storage (set by web app after login)
  const { firebaseConfig } = await chrome.storage.local.get('firebaseConfig');
  
  if (firebaseConfig && firebaseConfig.apiKey) {
    return firebaseConfig;
  }

  // No config available - extension needs web app to sync credentials first
  console.warn('Firebase config not found. User needs to log in via web app first.');
  return null;
};

let app: any = null;
let db: any = null;
let auth: any = null;
let isAuthenticated = false;

export const initFirebase = async () => {
  if (app && isAuthenticated) return { app, db, auth };

  const config = await getFirebaseConfig();
  
  if (!config || !config.apiKey) {
    console.warn('Firebase config not found. Extension will work in limited mode.');
    return { app: null, db: null, auth: null };
  }

  app = getApps().length === 0 ? initializeApp(config) : getApp();
  db = getFirestore(app);
  auth = getAuth(app);

  // Try to authenticate using the ID token from web app
  // Since we can't use ID token directly, we'll use Firestore REST API instead
  // But first, let's check if we can get the user ID from storage
  const { userId, authToken } = await chrome.storage.local.get(['userId', 'authToken']);
  
  if (userId && authToken) {
    // Store userId for use in Firestore writes
    // Note: We can't authenticate the Firebase client SDK with just an ID token
    // So we'll need to use the REST API or the backend API
    console.log('[Firebase] User ID and token available, but client SDK requires custom token');
    console.log('[Firebase] Will use REST API or backend API for writes');
  }

  return { app, db, auth };
};

export const getCurrentUserId = async (): Promise<string | null> => {
  const { auth: firebaseAuth } = await initFirebase();
  
  // First try to get from storage (synced from web app)
  const { userId } = await chrome.storage.local.get('userId');
  if (userId) {
    return userId;
  }
  
  if (!firebaseAuth) {
    return null;
  }

  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(firebaseAuth, (user) => {
      unsubscribe();
      if (user) {
        // Store userId for offline use
        chrome.storage.local.set({ userId: user.uid });
        resolve(user.uid);
      } else {
        resolve(null);
      }
    });
  });
};

// Helper to save session using Firestore REST API with ID token
export const saveSessionViaREST = async (sessionData: any): Promise<string | null> => {
  const { userId, authToken, firebaseConfig } = await chrome.storage.local.get([
    'userId',
    'authToken',
    'firebaseConfig',
  ]);

  if (!userId || !authToken || !firebaseConfig) {
    console.error('[Firebase REST] Missing credentials');
    return null;
  }

  try {
    // Use Firestore REST API
    const projectId = firebaseConfig.projectId;
    const url = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents/sessions`;
    
    // Convert session data to Firestore document format
    // Firestore REST API expects timestamps in RFC3339 format
    const formatTimestamp = (dateStr: string) => {
      // If already in ISO format, use it; otherwise convert
      const date = new Date(dateStr);
      return date.toISOString();
    };
    
    const firestoreDoc = {
      fields: {
        userId: { stringValue: sessionData.userId },
        startTime: { timestampValue: formatTimestamp(sessionData.startTime) },
        endTime: { timestampValue: formatTimestamp(sessionData.endTime) },
        duration: { integerValue: String(sessionData.duration) },
        topic: { stringValue: sessionData.topic },
        domains: {
          arrayValue: {
            values: sessionData.domains.map((d: string) => ({ stringValue: d })),
          },
        },
        focusScore: { doubleValue: sessionData.focusScore },
        productivityScore: { integerValue: String(sessionData.productivityScore) },
        tabSwitches: { integerValue: String(sessionData.tabSwitches) },
        activeTime: { integerValue: String(sessionData.activeTime) },
        idleTime: { integerValue: String(sessionData.idleTime) },
        xpEarned: { integerValue: String(sessionData.xpEarned) },
        source: { stringValue: sessionData.source },
        platform: { stringValue: sessionData.platform || 'chrome-extension' },
        createdAt: { timestampValue: new Date().toISOString() },
        updatedAt: { timestampValue: new Date().toISOString() },
      },
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify(firestoreDoc),
    });

    if (response.ok) {
      const result = await response.json();
      // Extract document ID from the response
      const docId = result.name.split('/').pop();
      return docId;
    } else {
      const errorText = await response.text();
      console.error('[Firebase REST] Error saving session:', response.status, errorText);
      return null;
    }
  } catch (error) {
    console.error('[Firebase REST] Exception saving session:', error);
    return null;
  }
};

export { Timestamp };

