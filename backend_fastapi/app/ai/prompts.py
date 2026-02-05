"""Prompt templates for OpenAI integration."""

SESSION_SUMMARY_PROMPT = """Summarize this study session in 1-2 sentences:

Topic: {topic}
Duration: {duration} minutes
Sites visited: {domains}
Productivity score: {productivity}/100
Activity type: {activity}

Be encouraging and mention any notable achievements. Keep it brief and positive."""

TASK_BREAKDOWN_PROMPT = """Break down this task into smaller, actionable subtasks:

Task: {title}
Description: {description}
Estimated time: {estimated} minutes

For each subtask, provide:
1. A clear, actionable title
2. Brief description (1 sentence)
3. Estimated time in minutes
4. Priority (high/medium/low)

Format as a numbered list. Include 3-7 subtasks.
At the end, add 1-2 suggestions for completing this task effectively."""

WEEKLY_SUMMARY_PROMPT = """Generate a motivating weekly productivity summary based on these stats:

Total study time: {hours} hours
Sessions completed: {sessions}
Average productivity: {productivity}/100
Top topics: {topics}
Current streak: {streak} days
XP earned: {xp}

Include:
1. A brief encouraging summary (2-3 sentences)
2. Key achievements or highlights
3. One specific area for improvement
4. One actionable suggestion for next week

Keep the tone supportive and motivating."""

PRODUCTIVITY_INSIGHTS_PROMPT = """Analyze this user's productivity patterns:

Study hours by day: {daily_hours}
Most productive hours: {best_hours}
Top topics: {topics}
Average session length: {avg_session} minutes
Distraction rate: {distraction_rate}%

Provide:
1. 3 key insights about their study patterns
2. 2-3 specific, actionable recommendations
3. One encouraging observation

Be specific and data-driven in your analysis."""

GOAL_SETTING_PROMPT = """Help set realistic study goals based on this user's history:

Current weekly average: {current_hours} hours
Best week: {best_week} hours
Study streak: {streak} days
Level: {level}

Suggest:
1. A realistic weekly hour goal
2. A stretch goal for motivated weeks
3. 2-3 specific habits to build
4. One milestone to work toward

Keep suggestions achievable but challenging."""
