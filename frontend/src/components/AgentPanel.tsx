import { useStore } from '../store/useStore';

const AgentPanel = () => {
  const { agents, workflowDescription } = useStore();

  return (
    <div className="card">
      <div className="card__header">
        <h2 className="card__title">Agent Team</h2>
      </div>
      
      <div className="agent-panel">
        {agents.length > 0 ? (
          agents.map((agent, index) => (
            <div key={index} className="agent-card">
              <div className="agent-card__name">{agent.name}</div>
              <div className="agent-card__role">{agent.role}</div>
              <div className="agent-card__description">{agent.description}</div>
            </div>
          ))
        ) : (
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
            Loading agents...
          </p>
        )}
      </div>

      {workflowDescription && (
        <div style={{ marginTop: '1rem' }}>
          <h3 style={{ 
            fontSize: '0.875rem', 
            color: 'var(--color-text-secondary)', 
            marginBottom: '0.5rem' 
          }}>
            Workflow
          </h3>
          <div className="workflow-description">{workflowDescription}</div>
        </div>
      )}
    </div>
  );
};

export default AgentPanel;
