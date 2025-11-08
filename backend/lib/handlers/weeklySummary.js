"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateWeeklySummary = generateWeeklySummary;
const admin = __importStar(require("firebase-admin"));
const openai_1 = __importDefault(require("openai"));
const openai = new openai_1.default({
    apiKey: process.env.OPENAI_API_KEY,
});
async function generateWeeklySummary() {
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
            if (sessionsSnapshot.empty)
                continue;
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
    }
    catch (error) {
        console.error('Error generating weekly summaries:', error);
    }
}
function calculateTopTopics(sessions) {
    const topicMap = {};
    sessions.forEach(session => {
        const topic = session.topic || 'General Study';
        topicMap[topic] = (topicMap[topic] || 0) + (session.duration / 60);
    });
    return Object.entries(topicMap)
        .map(([topic, minutes]) => ({ topic, minutes }))
        .sort((a, b) => b.minutes - a.minutes)
        .slice(0, 5);
}
async function generateWeeklySummaryText(data) {
    try {
        const prompt = `Generate an encouraging weekly study summary for ${data.userName}:
- Total study time: ${data.totalHours.toFixed(1)} hours
- Sessions completed: ${data.totalSessions}
- Average focus: ${Math.round(data.avgFocusScore * 100)}%
- Top topics: ${data.topTopics.map((t) => t.topic).join(', ')}

Write a brief, motivating summary (2-3 sentences) highlighting their achievements and encouraging continued progress.`;
        const completion = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [{ role: 'user', content: prompt }],
            max_tokens: 150,
            temperature: 0.7,
        });
        return completion.choices[0]?.message?.content || 'Great work this week! Keep up the momentum.';
    }
    catch (error) {
        console.error('Error generating weekly summary text:', error);
        return 'Great work this week! Keep up the momentum.';
    }
}
//# sourceMappingURL=weeklySummary.js.map