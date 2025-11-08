import { Request, Response } from 'express';
import * as admin from 'firebase-admin';

export async function handleCreateSession(req: Request, res: Response) {
  try {
    const sessionData = req.body;

    // Validate required fields
    if (!sessionData.userId || !sessionData.startTime || !sessionData.duration) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Create session document
    const sessionRef = await admin.firestore().collection('sessions').add({
      ...sessionData,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    res.status(201).json({
      success: true,
      sessionId: sessionRef.id,
    });
  } catch (error) {
    console.error('Error creating session:', error);
    res.status(500).json({ error: 'Failed to create session' });
  }
}

