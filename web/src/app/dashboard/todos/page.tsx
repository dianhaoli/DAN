'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { useState } from 'react';
import type { Todo } from '@dan/shared';

export default function TodosPage() {
  const { user } = useAuthContext();
  const [newTodo, setNewTodo] = useState('');
  const [todos, setTodos] = useState<Todo[]>([
    {
      id: '1',
      userId: user?.id || '',
      title: 'Review Python data structures',
      estimatedMinutes: 30,
      status: 'pending',
      priority: 'high',
      xpReward: 50,
      createdAt: new Date(),
      updatedAt: new Date(),
    },
    {
      id: '2',
      userId: user?.id || '',
      title: 'Complete calculus problem set',
      estimatedMinutes: 60,
      status: 'in_progress',
      priority: 'medium',
      xpReward: 100,
      createdAt: new Date(),
      updatedAt: new Date(),
    },
  ]);

  const handleAddTodo = () => {
    if (!newTodo.trim()) return;

    const todo: Todo = {
      id: Date.now().toString(),
      userId: user?.id || '',
      title: newTodo,
      status: 'pending',
      priority: 'medium',
      xpReward: 25,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    setTodos([...todos, todo]);
    setNewTodo('');
  };

  const toggleTodo = (id: string) => {
    setTodos(
      todos.map((todo) =>
        todo.id === id
          ? {
              ...todo,
              status: todo.status === 'completed' ? 'pending' : 'completed',
              completedAt: todo.status === 'completed' ? undefined : new Date(),
            }
          : todo
      )
    );
  };

  if (!user) return null;

  const pendingTodos = todos.filter((t) => t.status !== 'completed');
  const completedTodos = todos.filter((t) => t.status === 'completed');

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Study To-Dos</h1>
          <p className="text-gray-600 mt-1">Plan your study sessions and track completion.</p>
        </div>

        {/* Add Todo */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddTodo()}
              placeholder="What do you want to study?"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={handleAddTodo}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
            >
              Add
            </button>
          </div>
        </div>

        {/* Pending Todos */}
        {pendingTodos.length > 0 && (
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">To Do</h3>
            <div className="space-y-3">
              {pendingTodos.map((todo) => (
                <TodoItem key={todo.id} todo={todo} onToggle={toggleTodo} />
              ))}
            </div>
          </div>
        )}

        {/* Completed Todos */}
        {completedTodos.length > 0 && (
          <div className="bg-white rounded-2xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Completed</h3>
            <div className="space-y-3">
              {completedTodos.map((todo) => (
                <TodoItem key={todo.id} todo={todo} onToggle={toggleTodo} />
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

function TodoItem({ todo, onToggle }: { todo: Todo; onToggle: (id: string) => void }) {
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
      className={`flex items-center gap-4 p-4 border border-gray-200 rounded-xl hover:border-primary-300 transition-colors ${
        todo.status === 'completed' ? 'opacity-60' : ''
      }`}
    >
      <button
        onClick={() => onToggle(todo.id)}
        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
          todo.status === 'completed'
            ? 'bg-primary-600 border-primary-600'
            : 'border-gray-300 hover:border-primary-500'
        }`}
      >
        {todo.status === 'completed' && <span className="text-white text-sm">✓</span>}
      </button>

      <div className="flex-1">
        <div className={`font-medium ${todo.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'}`}>
          {todo.title}
        </div>
        <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
          {todo.estimatedMinutes && <span>⏱️ {todo.estimatedMinutes}min</span>}
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getPriorityColor()}`}>
            {todo.priority}
          </span>
        </div>
      </div>

      <div className="text-sm font-medium text-primary-600">+{todo.xpReward} XP</div>
    </div>
  );
}

