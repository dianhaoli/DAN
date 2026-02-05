/**
 * Sync Firebase config and user ID to Chrome extension via localStorage
 * The extension content script will read from localStorage and sync to background
 */

let refreshInterval: ReturnType<typeof setInterval> | null = null;

export async function syncExtensionCredentials() {
  if (typeof window === 'undefined') return;

  const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
  };

  // Get user ID and auth token from Firebase Auth
  const { auth } = await import('./firebase');
  const user = auth.currentUser;

  if (!user) {
    // Clear credentials if user logged out
    localStorage.removeItem('dan_extension_config');
    localStorage.removeItem('dan_extension_userId');
    localStorage.removeItem('dan_extension_authToken');
    localStorage.removeItem('dan_extension_tokenExpiry');
    // Stop refresh interval
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
    return;
  }

  // Get the ID token for authentication (force refresh to ensure it's valid)
  let idToken: string | null = null;
  try {
    // Force refresh to get a fresh token
    idToken = await user.getIdToken(true);
  } catch (error) {
    console.error('Failed to get ID token:', error);
  }

  // Store in localStorage (extension content script will read this)
  try {
    localStorage.setItem('dan_extension_config', JSON.stringify(firebaseConfig));
    localStorage.setItem('dan_extension_userId', user.uid);
    if (idToken) {
      localStorage.setItem('dan_extension_authToken', idToken);
      // Store token expiry (tokens expire after 1 hour, refresh at 50 minutes)
      const expiryTime = Date.now() + (50 * 60 * 1000);
      localStorage.setItem('dan_extension_tokenExpiry', expiryTime.toString());
    }
    console.log('[ExtensionSync] Credentials stored in localStorage');
  } catch (error) {
    console.error('Failed to store extension credentials:', error);
  }

  // Set up automatic token refresh every 50 minutes (tokens expire after 60 minutes)
  if (!refreshInterval) {
    refreshInterval = setInterval(async () => {
      console.log('[ExtensionSync] Refreshing auth token...');
      await syncExtensionCredentials();
    }, 50 * 60 * 1000); // 50 minutes
  }
}

/**
 * Force refresh the auth token for the extension
 * Call this when the extension reports token issues
 */
export async function forceRefreshExtensionToken(): Promise<boolean> {
  if (typeof window === 'undefined') return false;

  const { auth } = await import('./firebase');
  const user = auth.currentUser;

  if (!user) {
    console.warn('[ExtensionSync] No user logged in');
    return false;
  }

  try {
    const idToken = await user.getIdToken(true); // Force refresh
    localStorage.setItem('dan_extension_authToken', idToken);
    const expiryTime = Date.now() + (50 * 60 * 1000);
    localStorage.setItem('dan_extension_tokenExpiry', expiryTime.toString());
    console.log('[ExtensionSync] Token force refreshed');
    return true;
  } catch (error) {
    console.error('[ExtensionSync] Failed to force refresh token:', error);
    return false;
  }
}

