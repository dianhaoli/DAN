import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import express from 'express';
import cors from 'cors';

// Initialize Firebase Admin
admin.initializeApp();

// Import handlers
import { handleCreateSession } from './handlers/sessions';
import { handleGenerateAISummary } from './handlers/ai';
import { checkAndAwardBadges } from './handlers/gamification';
import { generateWeeklySummary } from './handlers/weeklySummary';
import { updateLeaderboards } from './handlers/leaderboards';

// Express API
const app = express();
app.use(cors({ origin: true }));
app.use(express.json());

// API Routes
app.post('/api/sessions', handleCreateSession);

// Export Express API as Cloud Function
export const api = functions.https.onRequest(app);

// Firestore Triggers
export const onSessionCreate = functions.firestore
  .document('sessions/{sessionId}')
  .onCreate(async (snap, context) => {
    const session = snap.data();
    const { userId } = session;

    // Update user stats
    const userRef = admin.firestore().doc(`users/${userId}`);
    const statsRef = admin.firestore().doc(`userStats/${userId}`);

    await admin.firestore().runTransaction(async (transaction) => {
      const userDoc = await transaction.get(userRef);
      const statsDoc = await transaction.get(statsRef);

      const currentXP = userDoc.data()?.xp || 0;
      const currentStudyTime = userDoc.data()?.totalStudyTime || 0;

      // Update user XP and study time
      transaction.update(userRef, {
        xp: currentXP + session.xpEarned,
        totalStudyTime: currentStudyTime + (session.duration / 60),
        updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      });

      // Update user stats
      if (statsDoc.exists()) {
        transaction.update(statsRef, {
          totalSessions: admin.firestore.FieldValue.increment(1),
          totalHours: admin.firestore.FieldValue.increment(session.duration / 3600),
        });
      } else {
        transaction.set(statsRef, {
          userId,
          totalSessions: 1,
          totalHours: session.duration / 3600,
          averageFocusScore: session.focusScore,
          averageProductivityScore: session.productivityScore || 0,
          topicDistribution: {},
          studyHeatmap: {},
          weeklyTrend: [],
        });
      }
    });

    // Check for badge awards
    await checkAndAwardBadges(userId);

    // Create activity feed item
    await admin.firestore().collection('activities').add({
      userId,
      userName: userDoc.data()?.displayName || 'User',
      userPhoto: userDoc.data()?.photoURL || null,
      type: 'session_complete',
      sessionId: snap.id,
      topic: session.topic,
      duration: session.duration,
      xpEarned: session.xpEarned,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      reactions: {},
    });

    // Generate AI summary (async, non-blocking)
    handleGenerateAISummary(snap.id, userId, session).catch(console.error);
  });

// Scheduled Functions
export const updateLeaderboardsDaily = functions.pubsub
  .schedule('every day 00:00')
  .timeZone('America/New_York')
  .onRun(async () => {
    await updateLeaderboards();
  });

export const generateWeeklySummaries = functions.pubsub
  .schedule('every sunday 23:59')
  .timeZone('America/New_York')
  .onRun(async () => {
    await generateWeeklySummary();
  });

// Callable Functions
export const addFriend = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }

  const userId = context.auth.uid;
  const { friendId } = data;

  // Add friend to user's friends list
  await admin.firestore().doc(`users/${userId}`).update({
    friends: admin.firestore.FieldValue.arrayUnion(friendId),
  });

  return { success: true };
});

export const removeFriend = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
  }

  const userId = context.auth.uid;
  const { friendId } = data;

  await admin.firestore().doc(`users/${userId}`).update({
    friends: admin.firestore.FieldValue.arrayRemove(friendId),
  });

  return { success: true };
});

