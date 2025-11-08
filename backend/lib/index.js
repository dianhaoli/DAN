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
exports.removeFriend = exports.addFriend = exports.generateWeeklySummaries = exports.updateLeaderboardsDaily = exports.onSessionCreate = exports.api = void 0;
const functions = __importStar(require("firebase-functions"));
const admin = __importStar(require("firebase-admin"));
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
// Initialize Firebase Admin
admin.initializeApp();
// Import handlers
const sessions_1 = require("./handlers/sessions");
const ai_1 = require("./handlers/ai");
const gamification_1 = require("./handlers/gamification");
const weeklySummary_1 = require("./handlers/weeklySummary");
const leaderboards_1 = require("./handlers/leaderboards");
// Express API
const app = (0, express_1.default)();
app.use((0, cors_1.default)({ origin: true }));
app.use(express_1.default.json());
// API Routes
app.post('/api/sessions', sessions_1.handleCreateSession);
// Export Express API as Cloud Function
exports.api = functions.https.onRequest(app);
// Firestore Triggers
exports.onSessionCreate = functions.firestore
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
        }
        else {
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
    await (0, gamification_1.checkAndAwardBadges)(userId);
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
    (0, ai_1.handleGenerateAISummary)(snap.id, userId, session).catch(console.error);
});
// Scheduled Functions
exports.updateLeaderboardsDaily = functions.pubsub
    .schedule('every day 00:00')
    .timeZone('America/New_York')
    .onRun(async () => {
    await (0, leaderboards_1.updateLeaderboards)();
});
exports.generateWeeklySummaries = functions.pubsub
    .schedule('every sunday 23:59')
    .timeZone('America/New_York')
    .onRun(async () => {
    await (0, weeklySummary_1.generateWeeklySummary)();
});
// Callable Functions
exports.addFriend = functions.https.onCall(async (data, context) => {
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
exports.removeFriend = functions.https.onCall(async (data, context) => {
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
//# sourceMappingURL=index.js.map