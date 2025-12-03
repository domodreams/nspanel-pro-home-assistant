/**
 * NSPanel Pro Configuration Card
 * A Lovelace card for configuring NSPanel Pro panels
 */

class NSPanelProConfigCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._entities = {
      lights: [],
      covers: [],
      climates: [],
    };
    this._selectedEntities = {
      lights: [],
      covers: [],
      climates: [],
    };
  }

  static getConfigElement() {
    return document.createElement('nspanelpro-config-card-editor');
  }

  static getStubConfig() {
    return {
      title: 'NSPanel Pro Configuration',
      panel_id: 'panel1',
    };
  }

  setConfig(config) {
    this._config = {
      title: 'NSPanel Pro Configuration',
      panel_id: 'panel1',
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._updateEntities();
    this._render();
  }

  _updateEntities() {
    if (!this._hass) return;

    this._entities = {
      lights: Object.keys(this._hass.states)
        .filter((e) => e.startsWith('light.'))
        .map((e) => ({
          entity_id: e,
          name: this._hass.states[e].attributes.friendly_name || e,
          state: this._hass.states[e].state,
        })),
      covers: Object.keys(this._hass.states)
        .filter((e) => e.startsWith('cover.'))
        .map((e) => ({
          entity_id: e,
          name: this._hass.states[e].attributes.friendly_name || e,
          state: this._hass.states[e].state,
        })),
      climates: Object.keys(this._hass.states)
        .filter((e) => e.startsWith('climate.'))
        .map((e) => ({
          entity_id: e,
          name: this._hass.states[e].attributes.friendly_name || e,
          state: this._hass.states[e].state,
        })),
    };
  }

  _toggleEntity(type, entityId) {
    const index = this._selectedEntities[type].indexOf(entityId);
    if (index === -1) {
      this._selectedEntities[type].push(entityId);
    } else {
      this._selectedEntities[type].splice(index, 1);
    }
    this._render();
  }

  _publishConfig() {
    if (!this._hass) return;

    const config = {
      panel_id: this._config.panel_id,
      entities: this._selectedEntities,
      timestamp: new Date().toISOString(),
    };

    // Publish configuration to MQTT
    this._hass.callService('mqtt', 'publish', {
      topic: `domodreams/nspanelpro/config/${this._config.panel_id}`,
      payload: JSON.stringify(config),
      retain: true,
    });

    this._showNotification('Configuration published to panel!');
  }

  _showNotification(message) {
    const event = new CustomEvent('hass-notification', {
      detail: { message },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  _render() {
    const styles = `
      <style>
        :host {
          display: block;
        }
        .card {
          background: var(--ha-card-background, var(--card-background-color, white));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
          padding: 16px;
          color: var(--primary-text-color);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid var(--divider-color);
        }
        .title {
          font-size: 1.2em;
          font-weight: 500;
        }
        .panel-id {
          font-size: 0.85em;
          color: var(--secondary-text-color);
          background: var(--primary-color);
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
        }
        .section {
          margin-bottom: 16px;
        }
        .section-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          margin-bottom: 8px;
          color: var(--primary-color);
        }
        .section-header .icon {
          width: 20px;
          height: 20px;
        }
        .entity-list {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 8px;
        }
        .entity-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          border: 2px solid transparent;
        }
        .entity-item:hover {
          background: var(--primary-color);
          color: white;
        }
        .entity-item.selected {
          border-color: var(--primary-color);
          background: rgba(var(--rgb-primary-color), 0.1);
        }
        .entity-item .checkbox {
          width: 18px;
          height: 18px;
          border: 2px solid var(--primary-color);
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .entity-item.selected .checkbox {
          background: var(--primary-color);
        }
        .entity-item.selected .checkbox::after {
          content: '✓';
          color: white;
          font-size: 12px;
        }
        .entity-name {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .entity-state {
          font-size: 0.8em;
          color: var(--secondary-text-color);
        }
        .entity-item:hover .entity-state {
          color: rgba(255,255,255,0.8);
        }
        .actions {
          display: flex;
          gap: 8px;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--divider-color);
        }
        .btn {
          flex: 1;
          padding: 12px 16px;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 1em;
          font-weight: 500;
          transition: all 0.2s ease;
        }
        .btn-primary {
          background: var(--primary-color);
          color: white;
        }
        .btn-primary:hover {
          opacity: 0.9;
        }
        .btn-secondary {
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
        }
        .btn-secondary:hover {
          background: var(--primary-color);
          color: white;
        }
        .stats {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }
        .stat {
          flex: 1;
          text-align: center;
          padding: 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }
        .stat-value {
          font-size: 1.5em;
          font-weight: bold;
          color: var(--primary-color);
        }
        .stat-label {
          font-size: 0.85em;
          color: var(--secondary-text-color);
        }
        .mqtt-info {
          font-size: 0.85em;
          color: var(--secondary-text-color);
          background: var(--secondary-background-color);
          padding: 8px 12px;
          border-radius: 8px;
          margin-bottom: 16px;
        }
        .mqtt-info code {
          background: var(--primary-color);
          color: white;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: monospace;
        }
      </style>
    `;

    const lightIcon = `<svg class="icon" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7M9 21v-1h6v1a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1Z"/></svg>`;
    const coverIcon = `<svg class="icon" viewBox="0 0 24 24" fill="currentColor"><path d="M3 4h18v2H3V4m0 4h18v2H3V8m0 4h18v2H3v-2m0 4h18v2H3v-2m0 4h18v2H3v-2Z"/></svg>`;
    const climateIcon = `<svg class="icon" viewBox="0 0 24 24" fill="currentColor"><path d="M17.66 11.2c-.23-.3-.51-.56-.77-.82-.67-.6-1.43-1.03-2.07-1.66C13.33 7.26 13 4.85 13.95 3c-.95.23-1.78.75-2.49 1.32-2.59 2.08-3.61 5.75-2.39 8.9.04.1.08.2.08.33 0 .22-.15.42-.35.5-.23.1-.47.04-.66-.12a.58.58 0 0 1-.14-.17c-1.13-1.43-1.31-3.48-.55-5.12C5.78 10 4.87 12.3 5 14.47c.06.5.12 1 .29 1.5.14.6.41 1.2.71 1.73 1.08 1.73 2.95 2.97 4.96 3.22 2.14.27 4.43-.12 6.07-1.6 1.83-1.66 2.47-4.32 1.53-6.6l-.13-.26c-.21-.46-.77-1.26-.77-1.26m-3.16 6.3c-.28.24-.74.5-1.1.6-1.12.4-2.24-.16-2.9-.82 1.19-.28 1.9-1.16 2.11-2.05.17-.8-.15-1.46-.28-2.23-.12-.74-.1-1.37.17-2.06.19.38.39.76.63 1.06.77 1 1.98 1.44 2.24 2.8.04.14.06.28.06.43.03.82-.33 1.72-.93 2.27Z"/></svg>`;

    const renderEntityList = (type, entities, icon) => {
      if (entities.length === 0) {
        return `<div style="color: var(--secondary-text-color); font-style: italic;">No ${type} entities found</div>`;
      }
      return `
        <div class="entity-list">
          ${entities
            .map(
              (e) => `
            <div class="entity-item ${this._selectedEntities[type].includes(e.entity_id) ? 'selected' : ''}" 
                 data-type="${type}" 
                 data-entity="${e.entity_id}">
              <div class="checkbox"></div>
              <span class="entity-name">${e.name}</span>
              <span class="entity-state">${e.state}</span>
            </div>
          `
            )
            .join('')}
        </div>
      `;
    };

    const totalSelected =
      this._selectedEntities.lights.length +
      this._selectedEntities.covers.length +
      this._selectedEntities.climates.length;

    this.shadowRoot.innerHTML = `
      ${styles}
      <div class="card">
        <div class="header">
          <span class="title">${this._config.title}</span>
          <span class="panel-id">${this._config.panel_id}</span>
        </div>

        <div class="mqtt-info">
          MQTT Base Topic: <code>domodreams/nspanelpro/</code>
        </div>

        <div class="stats">
          <div class="stat">
            <div class="stat-value">${this._entities.lights.length}</div>
            <div class="stat-label">Lights</div>
          </div>
          <div class="stat">
            <div class="stat-value">${this._entities.covers.length}</div>
            <div class="stat-label">Covers</div>
          </div>
          <div class="stat">
            <div class="stat-value">${this._entities.climates.length}</div>
            <div class="stat-label">Climates</div>
          </div>
          <div class="stat">
            <div class="stat-value">${totalSelected}</div>
            <div class="stat-label">Selected</div>
          </div>
        </div>

        <div class="section">
          <div class="section-header">${lightIcon} Lights</div>
          ${renderEntityList('lights', this._entities.lights, lightIcon)}
        </div>

        <div class="section">
          <div class="section-header">${coverIcon} Covers</div>
          ${renderEntityList('covers', this._entities.covers, coverIcon)}
        </div>

        <div class="section">
          <div class="section-header">${climateIcon} Climate</div>
          ${renderEntityList('climates', this._entities.climates, climateIcon)}
        </div>

        <div class="actions">
          <button class="btn btn-secondary" id="clear-btn">Clear Selection</button>
          <button class="btn btn-primary" id="publish-btn">Publish to Panel</button>
        </div>
      </div>
    `;

    // Add event listeners
    this.shadowRoot.querySelectorAll('.entity-item').forEach((item) => {
      item.addEventListener('click', () => {
        const type = item.dataset.type;
        const entityId = item.dataset.entity;
        this._toggleEntity(type, entityId);
      });
    });

    this.shadowRoot.getElementById('publish-btn')?.addEventListener('click', () => {
      this._publishConfig();
    });

    this.shadowRoot.getElementById('clear-btn')?.addEventListener('click', () => {
      this._selectedEntities = { lights: [], covers: [], climates: [] };
      this._render();
    });
  }

  getCardSize() {
    return 6;
  }
}

// Card Editor
class NSPanelProConfigCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
  }

  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    this.innerHTML = `
      <style>
        .editor {
          padding: 16px;
        }
        .field {
          margin-bottom: 16px;
        }
        .field label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        .field input {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--card-background-color);
          color: var(--primary-text-color);
        }
      </style>
      <div class="editor">
        <div class="field">
          <label>Title</label>
          <input type="text" id="title" value="${this._config.title || 'NSPanel Pro Configuration'}">
        </div>
        <div class="field">
          <label>Panel ID</label>
          <input type="text" id="panel_id" value="${this._config.panel_id || 'panel1'}">
        </div>
      </div>
    `;

    this.querySelector('#title').addEventListener('input', (e) => {
      this._config = { ...this._config, title: e.target.value };
      this._fireConfigChanged();
    });

    this.querySelector('#panel_id').addEventListener('input', (e) => {
      this._config = { ...this._config, panel_id: e.target.value };
      this._fireConfigChanged();
    });
  }

  _fireConfigChanged() {
    const event = new CustomEvent('config-changed', {
      detail: { config: this._config },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }
}

// Register the cards
customElements.define('nspanelpro-config-card', NSPanelProConfigCard);
customElements.define('nspanelpro-config-card-editor', NSPanelProConfigCardEditor);

// Register with Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'nspanelpro-config-card',
  name: 'NSPanel Pro Config',
  description: 'Configure entities for your NSPanel Pro by DomoDreams',
  preview: true,
  documentationURL: 'https://github.com/domodreams/nspanelpro_integration',
});

console.info(
  '%c NSPANELPRO-CONFIG-CARD %c v1.0.0 %c by DomoDreams ',
  'color: white; background: #3498db; font-weight: bold;',
  'color: #3498db; background: white; font-weight: bold;',
  'color: white; background: #2ecc71; font-weight: bold;'
);
