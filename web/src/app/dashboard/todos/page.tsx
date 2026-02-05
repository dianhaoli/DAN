'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import { useState } from 'react';
import type { Todo } from '@dan/shared';
import { Navbar } from '@/components/navbar';
import { Clock, Trash2 } from 'lucide-react';
import { useTodos } from '@/hooks/useTodos';
import toast from 'react-hot-toast';

export default function TodosPage() {
  const { user } = useAuthContext();
  const { todos, loading, addTodo, updateTodo, deleteTodo } = useTodos(user?.id || null);
  const [newTodo, setNewTodo] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAddTodo = async () => {
    if (!newTodo.trim() || !user) return;

    setIsAdding(true);
    try {
      await addTodo({
        userId: user.id,
        title: newTodo.trim(),
        priority: 'medium',
      });
      setNewTodo('');
      toast.success('Todo added!');
    } catch (error: any) {
      console.error('Error adding todo:', error);
      const errorMessage = error?.message || 'Failed to add todo. Please try again.';
      toast.error(errorMessage);
    } finally {
      setIsAdding(false);
    }
  };

  const toggleTodo = async (id: string, currentStatus: string) => {
    try {
      await updateTodo(id, {
        status: currentStatus === 'completed' ? 'pending' : 'completed',
        completedAt: currentStatus === 'completed' ? undefined : new Date(),
      });
      toast.success(currentStatus === 'completed' ? 'Todo marked as pending' : 'Todo completed!');
    } catch (error) {
      console.error('Error updating todo:', error);
      toast.error('Failed to update todo. Please try again.');
    }
  };

  const handleDeleteTodo = async (id: string) => {
    if (!confirm('Are you sure you want to delete this todo?')) return;

    try {
      await deleteTodo(id);
      toast.success('Todo deleted');
    } catch (error) {
      console.error('Error deleting todo:', error);
      toast.error('Failed to delete todo. Please try again.');
    }
  };

  if (!user) return null;

  const pendingTodos = todos.filter((t) => t.status !== 'completed' && t.status !== 'cancelled');
  const completedTodos = todos.filter((t) => t.status === 'completed');

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8 md:px-6 lg:px-8 max-w-7xl space-y-6">
        <div>
          <h1 className="text-3xl font-semibold text-foreground">Study To-Dos</h1>
          <p className="text-muted-foreground mt-1">Plan your study sessions and track completion.</p>
        </div>

        {/* Add Todo */}
        <div className="rounded-2xl bg-card border border-border/40 p-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isAdding && handleAddTodo()}
              placeholder="What do you want to study?"
              disabled={isAdding}
              className="flex-1 px-4 py-3 border border-input rounded-xl focus:outline-none focus:ring-1 focus:ring-ring bg-background text-foreground disabled:opacity-50"
            />
            <button
              onClick={handleAddTodo}
              disabled={isAdding}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAdding ? 'Adding...' : 'Add'}
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <div className="text-center py-8 text-muted-foreground">Loading todos...</div>
          </div>
        )}

        {/* Pending Todos */}
        {!loading && pendingTodos.length > 0 && (
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">To Do ({pendingTodos.length})</h3>
            <div className="space-y-3">
              {pendingTodos.map((todo) => (
                <TodoItem key={todo.id} todo={todo} onToggle={toggleTodo} onDelete={handleDeleteTodo} />
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && pendingTodos.length === 0 && completedTodos.length === 0 && (
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <div className="text-center py-12">
              <p className="text-muted-foreground mb-2">No todos yet</p>
              <p className="text-sm text-muted-foreground">Add a todo above to get started!</p>
            </div>
          </div>
        )}

        {/* Completed Todos */}
        {!loading && completedTodos.length > 0 && (
          <div className="rounded-2xl bg-card border border-border/40 p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">Completed ({completedTodos.length})</h3>
            <div className="space-y-3">
              {completedTodos.map((todo) => (
                <TodoItem key={todo.id} todo={todo} onToggle={toggleTodo} onDelete={handleDeleteTodo} />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function TodoItem({ 
  todo, 
  onToggle, 
  onDelete 
}: { 
  todo: Todo; 
  onToggle: (id: string, status: string) => void;
  onDelete: (id: string) => void;
}) {
  const getPriorityColor = () => {
    switch (todo.priority) {
      case 'high':
        return 'text-red-600 bg-red-50';
      case 'medium':
        return 'text-amber-600 bg-amber-50';
      case 'low':
        return 'text-green-600 bg-green-50';
    }
  };

  return (
    <div
      className={`flex items-center gap-4 p-4 border border-border/40 rounded-xl hover:bg-accent/30 transition-colors ${
        todo.status === 'completed' ? 'opacity-60' : ''
      }`}
    >
      <button
        onClick={() => onToggle(todo.id, todo.status)}
        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors flex-shrink-0 ${
          todo.status === 'completed'
            ? 'bg-primary border-primary'
            : 'border-input hover:border-ring'
        }`}
      >
        {todo.status === 'completed' && <span className="text-white text-sm">✓</span>}
      </button>

      <div className="flex-1 min-w-0">
        <div className={`font-medium ${todo.status === 'completed' ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
          {todo.title}
        </div>
        <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground flex-wrap">
          {todo.estimatedMinutes && (
            <span className="inline-flex items-center gap-1">
              <Clock className="w-4 h-4" /> {todo.estimatedMinutes}min
            </span>
          )}
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor()}`}>
            {todo.priority}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="text-sm font-medium text-primary-600">+{todo.xpReward} XP</div>
        <button
          onClick={() => onDelete(todo.id)}
          className="p-1.5 text-muted-foreground hover:text-destructive transition-colors rounded hover:bg-destructive/10"
          aria-label="Delete todo"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

