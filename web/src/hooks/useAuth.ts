import { useEffect, useState } from 'react';
import { 
  User as FirebaseUser, 
  onAuthStateChanged, 
  signInWithPopup, 
  signOut as firebaseSignOut 
} from 'firebase/auth';
import { doc, getDoc, setDoc, serverTimestamp } from 'firebase/firestore';
import { auth, googleProvider, db } from '@/lib/firebase';
import type { User } from '@dan/shared';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setFirebaseUser(firebaseUser);
      
      if (firebaseUser) {
        // Fetch or create user document
        const userDoc = await getDoc(doc(db, 'users', firebaseUser.uid));
        
        if (userDoc.exists()) {
          setUser(userDoc.data() as User);
        } else {
          // Create new user document
          const newUser: User = {
            id: firebaseUser.uid,
            email: firebaseUser.email!,
            displayName: firebaseUser.displayName || 'Anonymous',
            photoURL: firebaseUser.photoURL || undefined,
            createdAt: new Date(),
            updatedAt: new Date(),
            xp: 0,
            level: 0,
            streak: 0,
            longestStreak: 0,
            totalStudyTime: 0,
            friends: [],
            isPublic: true,
          };
          
          await setDoc(doc(db, 'users', firebaseUser.uid), {
            ...newUser,
            createdAt: serverTimestamp(),
            updatedAt: serverTimestamp(),
          });
          
          setUser(newUser);
        }

        // Sync credentials with extension (and set up periodic refresh)
        try {
          const { syncExtensionCredentials } = await import('@/lib/extensionSync');
          await syncExtensionCredentials();
        } catch (error) {
          // Extension sync is optional, don't fail auth if it fails
          console.log('Extension sync failed (optional):', error);
        }
        
        // Also refresh token on page visibility change (when user returns to tab)
        const handleVisibilityChange = async () => {
          if (document.visibilityState === 'visible') {
            try {
              const { syncExtensionCredentials: refreshSync } = await import('@/lib/extensionSync');
              await refreshSync();
            } catch (e) {
              // Silent fail
            }
          }
        };
        document.addEventListener('visibilitychange', handleVisibilityChange);
      } else {
        setUser(null);
      }
      
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error('Error signing in with Google:', error);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      await firebaseSignOut(auth);
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  };

  const checkUsernameAvailable = async (username: string): Promise<boolean> => {
    const normalized = username.toLowerCase().trim();
    if (!normalized) return false;
    const usernameDoc = await getDoc(doc(db, 'usernames', normalized));
    return !usernameDoc.exists();
  };

  const setUsername = async (username: string): Promise<void> => {
    const normalized = username.toLowerCase().trim();
    if (!firebaseUser) {
      throw new Error('Not authenticated');
    }
    const isAvailable = await checkUsernameAvailable(normalized);
    if (!isAvailable) {
      throw new Error('Username already taken');
    }
    // Reserve username → userId mapping
    await setDoc(doc(db, 'usernames', normalized), {
      userId: firebaseUser.uid,
      createdAt: serverTimestamp(),
    });
    // Update user document with username
    await setDoc(
      doc(db, 'users', firebaseUser.uid),
      { username: normalized, updatedAt: serverTimestamp() },
      { merge: true }
    );
    // Update local state timestamp (username not in type; keep type-safe)
    setUser((prev) => (prev ? { ...prev, updatedAt: new Date() } : prev));
  };

  return {
    user,
    firebaseUser,
    loading,
    signInWithGoogle,
    signOut,
    setUsername,
    checkUsernameAvailable,
  };
}

