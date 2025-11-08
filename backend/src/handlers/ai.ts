import * as admin from 'firebase-admin';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function handleGenerateAISummary(
  sessionId: string,
  userId: string,
  sessionData: any
) {
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
  } catch (error) {
    console.error('Error generating AI summary:', error);
  }
}

function extractTopics(title: string, domains: string[]): string[] {
  const topics: Set<string> = new Set();

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
    if (domain.includes('python')) topics.add('python');
    if (domain.includes('javascript') || domain.includes('js')) topics.add('javascript');
    if (domain.includes('math')) topics.add('mathematics');
    if (domain.includes('leetcode') || domain.includes('hackerrank')) topics.add('coding');
  });

  return Array.from(topics);
}

