import { useStore } from '../store/useStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { SceneObject, LightingSetup, CameraSetup, ValidationIssue } from '../types';

const SceneDisplay = () => {
  const { currentScene, isLoading, error } = useStore();

  if (isLoading) {
    return (
      <div className="card">
        <div className="loading-overlay">
          <div className="loading-spinner" />
          <p className="loading-text">Agents are collaborating to create your scene...</p>
          <p className="loading-text" style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
            Orchestrator → Librarian → Architect → Material Scientist → Cinematographer → Critic
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  if (!currentScene) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--color-text-muted)' }}>
          <p>Enter a scene description above to get started.</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
            Example: "Create a cozy bedroom with a white bed, wooden desk, and warm morning light"
          </p>
        </div>
      </div>
    );
  }

  const { scene_data, validation_report, processing_time_ms, status } = currentScene;

  return (
    <div className="scene-display">
      {/* Status Header */}
      <div className="card">
        <div className="card__header">
          <h2 className="card__title">Scene Result</h2>
          <span className="processing-time">{processing_time_ms.toFixed(0)}ms</span>
        </div>
        <div className={`validation-status ${validation_report?.passed ? 'validation-status--passed' : 'validation-status--failed'}`}>
          <strong>{validation_report?.passed ? '✓ Validation Passed' : '✗ Validation Issues'}</strong>
          <span style={{ marginLeft: 'auto', fontSize: '0.875rem' }}>
            Status: {status}
          </span>
        </div>
      </div>

      {/* Scene Objects */}
      {scene_data?.objects && scene_data.objects.length > 0 && (
        <div className="card">
          <div className="card__header">
            <h2 className="card__title">Scene Objects ({scene_data.objects.length})</h2>
          </div>
          <div className="scene-objects">
            {scene_data.objects.map((obj) => (
              <ObjectCard key={obj.id} object={obj} />
            ))}
          </div>
        </div>
      )}

      {/* Lighting & Camera */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {scene_data?.lighting && (
          <div className="card">
            <LightingInfo lighting={scene_data.lighting} />
          </div>
        )}
        {scene_data?.camera && (
          <div className="card">
            <CameraInfo camera={scene_data.camera} />
          </div>
        )}
      </div>

      {/* Validation Issues */}
      {validation_report?.issues && validation_report.issues.length > 0 && (
        <div className="card validation-report">
          <div className="card__header">
            <h2 className="card__title">Validation Issues ({validation_report.issues.length})</h2>
          </div>
          <div className="validation-issues">
            {validation_report.issues.map((issue, index) => (
              <IssueItem key={index} issue={issue} />
            ))}
          </div>
        </div>
      )}

      {/* Final Report */}
      {validation_report?.final_report && (
        <div className="card">
          <div className="card__header">
            <h2 className="card__title">Final Report</h2>
          </div>
          <div className="final-report">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {validation_report.final_report}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
};

const ObjectCard = ({ object }: { object: SceneObject }) => {
  const statusClass = object.status === 'textured' ? 'object-card__status--textured' : 'object-card__status--placed';

  return (
    <div className="object-card">
      <div className="object-card__header">
        <span className="object-card__name">{object.name}</span>
        <span className={`object-card__status ${statusClass}`}>{object.status}</span>
      </div>
      <div className="object-card__details">
        {object.position && (
          <div className="object-card__detail">
            <span className="object-card__label">Position:</span>
            <span>({object.position.x.toFixed(2)}, {object.position.y.toFixed(2)}, {object.position.z.toFixed(2)})</span>
          </div>
        )}
        {object.material && (
          <div className="object-card__detail">
            <span className="object-card__label">Material:</span>
            <span>{object.material.name} ({object.material.shader_type})</span>
          </div>
        )}
        {object.asset_path && (
          <div className="object-card__detail">
            <span className="object-card__label">Asset:</span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'monospace' }}>{object.asset_path}</span>
          </div>
        )}
      </div>
    </div>
  );
};

const LightingInfo = ({ lighting }: { lighting: LightingSetup }) => {
  return (
    <div className="setup-info">
      <h3 className="setup-info__title">Lighting</h3>
      <div className="setup-info__item">
        <span className="setup-info__label">Lights</span>
        <span className="setup-info__value">{lighting.lights.length}</span>
      </div>
      <div className="setup-info__item">
        <span className="setup-info__label">Exposure</span>
        <span className="setup-info__value">{lighting.exposure}</span>
      </div>
      {lighting.hdri_map && (
        <div className="setup-info__item">
          <span className="setup-info__label">HDRI</span>
          <span className="setup-info__value" style={{ fontSize: '0.75rem' }}>{lighting.hdri_map}</span>
        </div>
      )}
      {lighting.lights.map((light, index) => (
        <div key={index} className="setup-info__item">
          <span className="setup-info__label">{light.name}</span>
          <span className="setup-info__value">{light.light_type} @ {light.color_temperature}K</span>
        </div>
      ))}
    </div>
  );
};

const CameraInfo = ({ camera }: { camera: CameraSetup }) => {
  return (
    <div className="setup-info">
      <h3 className="setup-info__title">Camera</h3>
      <div className="setup-info__item">
        <span className="setup-info__label">Focal Length</span>
        <span className="setup-info__value">{camera.focal_length}mm</span>
      </div>
      <div className="setup-info__item">
        <span className="setup-info__label">Aperture</span>
        <span className="setup-info__value">f/{camera.aperture}</span>
      </div>
      <div className="setup-info__item">
        <span className="setup-info__label">DOF</span>
        <span className="setup-info__value">{camera.depth_of_field ? 'Enabled' : 'Disabled'}</span>
      </div>
      <div className="setup-info__item">
        <span className="setup-info__label">Position</span>
        <span className="setup-info__value">
          ({camera.position.x.toFixed(1)}, {camera.position.y.toFixed(1)}, {camera.position.z.toFixed(1)})
        </span>
      </div>
    </div>
  );
};

const IssueItem = ({ issue }: { issue: ValidationIssue }) => {
  const severityClass = `issue-item__severity--${issue.severity}`;

  return (
    <div className="issue-item">
      <span className={`issue-item__severity ${severityClass}`}>{issue.severity}</span>
      <div>
        <div><strong>{issue.category}:</strong> {issue.description}</div>
        {issue.suggested_fix && (
          <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
            Fix: {issue.suggested_fix}
          </div>
        )}
      </div>
    </div>
  );
};

export default SceneDisplay;
