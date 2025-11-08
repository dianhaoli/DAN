import * as admin from 'firebase-admin';

export async function updateLeaderboards() {
  try {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    // Get all users
    const usersSnapshot = await admin.firestore().collection('users').get();
    const users = usersSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

    // Weekly hours leaderboard
    const sessionsSnapshot = await admin.firestore()
      .collection('sessions')
      .where('startTime', '>=', weekAgo.toISOString())
      .get();

    const userHours: Record<string, number> = {};
    sessionsSnapshot.docs.forEach(doc => {
      const session = doc.data();
      userHours[session.userId] = (userHours[session.userId] || 0) + (session.duration / 3600);
    });

    const hoursEntries = users
      .map((user: any, index) => ({
        userId: user.id,
        userName: user.displayName,
        userPhoto: user.photoURL,
        rank: 0,
        score: userHours[user.id] || 0,
        change: 0,
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 100)
      .map((entry, index) => ({ ...entry, rank: index + 1 }));

    await admin.firestore().doc('leaderboards/weekly-hours').set({
      id: 'weekly-hours',
      name: 'Weekly Hours',
      type: 'hours',
      period: 'weekly',
      scope: 'global',
      entries: hoursEntries,
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    // All-time XP leaderboard
    const xpEntries = users
      .map((user: any) => ({
        userId: user.id,
        userName: user.displayName,
        userPhoto: user.photoURL,
        rank: 0,
        score: user.xp || 0,
        change: 0,
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 100)
      .map((entry, index) => ({ ...entry, rank: index + 1 }));

    await admin.firestore().doc('leaderboards/alltime-xp').set({
      id: 'alltime-xp',
      name: 'All-Time XP',
      type: 'xp',
      period: 'all-time',
      scope: 'global',
      entries: xpEntries,
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    console.log('Leaderboards updated successfully');
  } catch (error) {
    console.error('Error updating leaderboards:', error);
  }
}

