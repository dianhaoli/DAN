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
exports.handleGenerateAISummary = handleGenerateAISummary;
const admin = __importStar(require("firebase-admin"));
const openai_1 = __importDefault(require("openai"));
const openai = new openai_1.default({
    apiKey: process.env.OPENAI_API_KEY,
});
async function handleGenerateAISummary(sessionId, userId, sessionData) {
    try {
        // Generate summary using GPT
        const prompt = `Summarize this study session in 1-2 sentences:
Topic: ${sessionData.topic}
Duration: ${Math.round(sessionData.duration / 60)} minutes
Domains visited: ${sessionData.domains?.join(', ') || 'N/A'}
Focus score: ${Math.round(sessionData.focusScore * 100)}%

Provide a concise, encouraging summary.`;
        const completion = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [{ role: 'user', content: prompt }],
            max_tokens: 100,
            temperature: 0.7,
        });
        const summary = completion.choices[0]?.message?.content || 'Study session completed.';
        // Extract topics (simple keyword extraction for MVP)
        const topics = extractTopics(sessionData.topic, sessionData.domains);
        // Save summary to Firestore
        await admin.firestore().collection('aiSummaries').add({
            sessionId,
            userId,
            summary,
            topics,
            sentiment: 'positive',
            generatedAt: admin.firestore.FieldValue.serverTimestamp(),
        });
        // Update session with AI summary
        await admin.firestore().doc(`sessions/${sessionId}`).update({
            aiSummary: summary,
            topics,
        });
    }
    catch (error) {
        console.error('Error generating AI summary:', error);
    }
}
function extractTopics(title, domains) {
    const topics = new Set();
    // Extract from title
    const keywords = ['python', 'javascript', 'math', 'physics', 'chemistry', 'biology',
        'history', 'english', 'coding', 'programming', 'data', 'machine learning'];
    const lowerTitle = title.toLowerCase();
    keywords.forEach(keyword => {
        if (lowerTitle.includes(keyword)) {
            topics.add(keyword);
        }
    });
    // Extract from domains
    domains?.forEach(domain => {
        if (domain.includes('python'))
            topics.add('python');
        if (domain.includes('javascript') || domain.includes('js'))
            topics.add('javascript');
        if (domain.includes('math'))
            topics.add('mathematics');
        if (domain.includes('leetcode') || domain.includes('hackerrank'))
            topics.add('coding');
    });
    return Array.from(topics);
}
//# sourceMappingURL=ai.js.map