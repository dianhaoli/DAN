import * as admin from 'firebase-admin';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function generateWeeklySummary() {
  try {
    const now = new Date();
    const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    // Get all users
    const usersSnapshot = await admin.firestore().collection('users').get();

    for (const userDoc of usersSnapshot.docs) {
      const userId = userDoc.id;
      const userData = userDoc.data();

      // Get sessions for the week
      const sessionsSnapshot = await admin.firestore()
        .collection('sessions')
        .where('userId', '==', userId)
        .where('startTime', '>=', weekStart.toISOString())
        .get();

      if (sessionsSnapshot.empty) continue;

      const sessions = sessionsSnapshot.docs.map(doc => doc.data());

      // Calculate stats
      const totalHours = sessions.reduce((sum, s) => sum + (s.duration / 3600), 0);
      const totalSessions = sessions.length;
      const avgFocusScore = sessions.reduce((sum, s) => sum + s.focusScore, 0) / sessions.length;
      
      const topTopics = calculateTopTopics(sessions);
      
      // Generate AI summary
      const aiSummary = await generateWeeklySummaryText({
        totalHours,
        totalSessions,
        avgFocusScore,
        topTopics,
        userName: userData.displayName,
      });

      // Save summary
      await admin.firestore().collection('weeklySummaries').add({
        userId,
        weekStart: admin.firestore.Timestamp.fromDate(weekStart),
        weekEnd: admin.firestore.Timestamp.fromDate(now),
        totalHours,
        totalSessions,
        averageFocusScore: avgFocusScore,
        averageProductivityScore: 0,
        xpEarned: sessions.reduce((sum, s) => sum + s.xpEarned, 0),
        newBadges: [],
        streakAtEnd: userData.streak || 0,
        topTopics,
        aiSummary,
        improvements: [],
        suggestions: [],
        focusTrend: 0,
        hoursTrend: 0,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
      });
    }

    console.log('Weekly summaries generated successfully');
  } catch (error) {
    console.error('Error generating weekly summaries:', error);
  }
}

function calculateTopTopics(sessions: any[]): Array<{ topic: string; minutes: number }> {
  const topicMap: Record<string, number> = {};

  sessions.forEach(session => {
    const topic = session.topic || 'General Study';
    topicMap[topic] = (topicMap[topic] || 0) + (session.duration / 60);
  });

  return Object.entries(topicMap)
    .map(([topic, minutes]) => ({ topic, minutes }))
    .sort((a, b) => b.minutes - a.minutes)
    .slice(0, 5);
}

async function generateWeeklySummaryText(data: any): Promise<string> {
  try {
    const prompt = `Generate an encouraging weekly study summary for ${data.userName}:
- Total study time: ${data.totalHours.toFixed(1)} hours
- Sessions completed: ${data.totalSessions}
- Average focus: ${Math.round(data.avgFocusScore * 100)}%
- Top topics: ${data.topTopics.map((t: any) => t.topic).join(', ')}

Write a brief, motivating summary (2-3 sentences) highlighting their achievements and encouraging continued progress.`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 150,
      temperature: 0.7,
    });

    return completion.choices[0]?.message?.content || 'Great work this week! Keep up the momentum.';
  } catch (error) {
    console.error('Error generating weekly summary text:', error);
    return 'Great work this week! Keep up the momentum.';
  }
}

