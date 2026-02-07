import { useEffect } from 'react';
import { useStore } from './store/useStore';
import api from './api/client';
import Header from './components/Header';
import PromptInput from './components/PromptInput';
import SceneDisplay from './components/SceneDisplay';
import AgentPanel from './components/AgentPanel';

function App() {
  const { setAgents } = useStore();

  useEffect(() => {
    // Fetch agents on load
    const fetchAgents = async () => {
      try {
        const response = await api.listAgents();
        setAgents(response.agents, response.workflow);
      } catch (error) {
        console.error('Failed to fetch agents:', error);
      }
    };

    fetchAgents();
  }, [setAgents]);

  return (
    <div className="app">
      <Header />
      <main className="main">
        <div className="scene-display">
          <PromptInput />
          <SceneDisplay />
        </div>
        <aside>
          <AgentPanel />
        </aside>
      </main>
    </div>
  );
}

export default App;
