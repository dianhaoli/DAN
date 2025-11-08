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
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateLeaderboards = updateLeaderboards;
const admin = __importStar(require("firebase-admin"));
async function updateLeaderboards() {
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
        const userHours = {};
        sessionsSnapshot.docs.forEach(doc => {
            const session = doc.data();
            userHours[session.userId] = (userHours[session.userId] || 0) + (session.duration / 3600);
        });
        const hoursEntries = users
            .map((user, index) => ({
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
            .map((user) => ({
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
    }
    catch (error) {
        console.error('Error updating leaderboards:', error);
    }
}
//# sourceMappingURL=leaderboards.js.map