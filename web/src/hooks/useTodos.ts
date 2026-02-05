import { useEffect, useState, useCallback } from 'react';
import { todosApi } from '@/lib/api';
import type { Todo } from '@dan/shared';

// Convert backend response (snake_case) to frontend format (camelCase)
const backendToFrontend = (backendTodo: any): Todo => ({
  id: backendTodo.id,
  userId: backendTodo.user_id,
  title: backendTodo.title,
  description: backendTodo.description,
  estimatedMinutes: backendTodo.estimated_minutes,
  dueDate: backendTodo.due_date ? new Date(backendTodo.due_date) : undefined,
  scheduledDate: backendTodo.scheduled_date ? new Date(backendTodo.scheduled_date) : undefined,
  status: backendTodo.status as 'pending' | 'in_progress' | 'completed' | 'cancelled',
  completedAt: backendTodo.completed_at ? new Date(backendTodo.completed_at) : undefined,
  linkedSessionId: backendTodo.linked_session_id,
  actualMinutes: backendTodo.actual_minutes,
  category: backendTodo.category,
  priority: backendTodo.priority as 'low' | 'medium' | 'high',
  xpReward: backendTodo.xp_reward,
  createdAt: new Date(backendTodo.created_at),
  updatedAt: new Date(backendTodo.updated_at),
});

// Convert frontend format (camelCase) to backend format (snake_case)
// Note: Only includes fields that TodoCreate schema accepts
const frontendToBackend = (todo: Partial<Todo>, forCreate: boolean = false): any => {
  const data: any = {};
  if (todo.title !== undefined) data.title = todo.title;
  if (todo.description !== undefined) data.description = todo.description;
  if (todo.estimatedMinutes !== undefined) data.estimated_minutes = todo.estimatedMinutes;
  if (todo.dueDate !== undefined) data.due_date = todo.dueDate?.toISOString();
  if (todo.scheduledDate !== undefined) data.scheduled_date = todo.scheduledDate?.toISOString();
  if (todo.category !== undefined) data.category = todo.category;
  if (todo.priority !== undefined) data.priority = todo.priority;
  
  // Status is only included for updates, not creates
  if (!forCreate && todo.status !== undefined) {
    data.status = todo.status;
  }
  
  return data;
};

export function useTodos(userId: string | null) {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchTodos = useCallback(async () => {
    if (!userId) {
      setTodos([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await todosApi.list({ limit: 100 });
      const todosData = response.todos.map(backendToFrontend);
      // Sort by createdAt (newest first)
      todosData.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
      setTodos(todosData);
    } catch (err) {
      console.error('Error fetching todos:', err);
      setError(err as Error);
      setTodos([]);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchTodos();
    
    // Poll for updates every 5 seconds (since we don't have real-time updates)
    const interval = setInterval(fetchTodos, 5000);
    
    return () => clearInterval(interval);
  }, [fetchTodos]);

  const addTodo = async (todo: Omit<Todo, 'id' | 'createdAt' | 'updatedAt'>): Promise<string> => {
    if (!userId) throw new Error('User not authenticated');

    try {
      // Only send fields that TodoCreate schema accepts (forCreate=true excludes status)
      const backendData = frontendToBackend(todo, true);
      
      console.log('Creating todo with data:', backendData);
      const response = await todosApi.create(backendData);
      const newTodo = backendToFrontend(response);
      
      // Refresh the list to get the latest todos
      await fetchTodos();
      
      return newTodo.id;
    } catch (err: any) {
      console.error('Error adding todo:', err);
      console.error('Error details:', {
        message: err?.message,
        stack: err?.stack,
      });
      throw err;
    }
  };

  const updateTodo = async (id: string, updates: Partial<Todo>): Promise<void> => {
    if (!userId) throw new Error('User not authenticated');

    try {
      // For updates, status is allowed (forCreate=false)
      const backendData = frontendToBackend(updates, false);
      await todosApi.update(id, backendData);
      
      // Refresh the list to get the latest todos
      await fetchTodos();
    } catch (err: any) {
      console.error('Error updating todo:', err);
      throw err;
    }
  };

  const deleteTodo = async (id: string): Promise<void> => {
    if (!userId) throw new Error('User not authenticated');

    try {
      await todosApi.delete(id);
      
      // Refresh the list to get the latest todos
      await fetchTodos();
    } catch (err) {
      console.error('Error deleting todo:', err);
      throw err;
    }
  };

  return {
    todos,
    loading,
    error,
    addTodo,
    updateTodo,
    deleteTodo,
  };
}
