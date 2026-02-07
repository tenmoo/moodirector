import { useState } from 'react';
import { useStore } from '../store/useStore';
import api from '../api/client';

const PromptInput = () => {
  const [prompt, setPrompt] = useState('');
  const [maxIterations, setMaxIterations] = useState(3);
  const { isLoading, setLoading, setCurrentScene, setError, addToHistory } = useStore();

  const handleSubmit = async () => {
    if (!prompt.trim() || isLoading) return;

    setLoading(true);
    setError(null);
    addToHistory(prompt);

    try {
      const response = await api.createScene({
        prompt: prompt.trim(),
        max_iterations: maxIterations,
      });
      setCurrentScene(response);
    } catch (error) {
      console.error('Failed to create scene:', error);
      setError(error instanceof Error ? error.message : 'Failed to create scene');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSubmit();
    }
  };

  return (
    <div className="card prompt-section">
      <div className="card__header">
        <h2 className="card__title">Scene Description</h2>
      </div>
      <textarea
        className="prompt-input"
        placeholder="Describe your 3D scene... (e.g., 'Create a cozy bedroom with a white bed, wooden desk, and warm morning light')"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isLoading}
      />
      <div className="prompt-actions">
        <button
          className={`btn btn--primary ${isLoading ? 'btn--loading' : ''}`}
          onClick={handleSubmit}
          disabled={!prompt.trim() || isLoading}
        >
          {isLoading ? 'Creating Scene...' : 'Create Scene'}
        </button>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Max Iterations:</span>
          <select
            value={maxIterations}
            onChange={(e) => setMaxIterations(Number(e.target.value))}
            disabled={isLoading}
            style={{
              background: 'var(--color-bg-tertiary)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-primary)',
              padding: '0.25rem 0.5rem',
            }}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4</option>
            <option value={5}>5</option>
          </select>
        </label>
      </div>
      <p style={{ 
        marginTop: '0.5rem', 
        fontSize: '0.75rem', 
        color: 'var(--color-text-muted)' 
      }}>
        Press Cmd+Enter to submit
      </p>
    </div>
  );
};

export default PromptInput;
