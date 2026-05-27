import { LitElement, html, css } from 'https://unpkg.com/lit-element@3.3.3/lit-element.js?module';

class DoorlockCard extends LitElement {
  static get properties() {
    return {
      _hass: { type: Object, state: true },
      _callActive: { type: Boolean, state: true },
      _deviceName: { type: String, state: true },
      _displayName: { type: String, state: true },
      _targetIp: { type: String, state: true },
      _floorLabel: { type: String, state: true },
      _positionDetail: { type: String, state: true },
      _cameraUrl: { type: String, state: true },
      _loadingFrame: { type: Boolean, state: true },
      _showCallPopup: { type: Boolean, state: true },
      _config: { type: Object },
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      .card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 16px;
        padding: 16px;
        color: #fff;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .header-title {
        font-size: 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .header-icon {
        font-size: 20px;
      }
      .status-badge {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        background: #4caf50;
      }
      .status-badge.active {
        background: #f44336;
        animation: pulse 1.5s infinite;
      }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
      }
      .door-list {
        display: grid;
        gap: 8px;
      }
      .door-item {
        display: flex;
        align-items: center;
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(255,255,255,0.08);
        cursor: pointer;
        transition: background 0.2s;
        gap: 10px;
      }
      .door-item:hover {
        background: rgba(255,255,255,0.15);
      }
      .door-item.offline {
        opacity: 0.5;
        cursor: default;
      }
      .door-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #4caf50;
        flex-shrink: 0;
      }
      .door-indicator.offline {
        background: #555;
      }
      .door-indicator.calling {
        background: #f44336;
        animation: pulse 1.5s infinite;
      }
      .door-info {
        flex: 1;
      }
      .door-name {
        font-size: 14px;
        font-weight: 500;
      }
      .door-location {
        font-size: 12px;
        color: rgba(255,255,255,0.6);
        margin-top: 2px;
      }
      .call-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 380px;
        background: #1a1a2e;
        border-radius: 16px;
        overflow: hidden;
        z-index: 9999;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5);
      }
      .popup-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: rgba(255,255,255,0.05);
        border-bottom: 1px solid rgba(255,255,255,0.1);
      }
      .popup-title {
        font-size: 14px;
        font-weight: 600;
      }
      .popup-close {
        background: none;
        border: none;
        color: rgba(255,255,255,0.6);
        font-size: 20px;
        cursor: pointer;
        padding: 0;
        line-height: 1;
      }
      .popup-video {
        width: 100%;
        aspect-ratio: 16/9;
        background: #000;
        display: flex;
        align-items: center;
        justify-content: center;
        color: rgba(255,255,255,0.3);
        font-size: 12px;
      }
      .popup-video img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      .popup-actions {
        display: flex;
        padding: 12px;
        gap: 8px;
      }
      .popup-btn {
        flex: 1;
        padding: 10px;
        border: none;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: opacity 0.2s;
      }
      .popup-btn:hover {
        opacity: 0.85;
      }
      .popup-btn.unlock {
        background: #4caf50;
        color: #fff;
      }
      .popup-btn.answer {
        background: #2196f3;
        color: #fff;
      }
      .popup-btn.hangup {
        background: #f44336;
        color: #fff;
      }
      .popup-btn:disabled {
        opacity: 0.4;
        cursor: default;
      }
      .overlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.6);
        z-index: 9998;
      }
    `;
  }

  setConfig(config) {
    this._config = config;
  }

  connectedCallback() {
    super.connectedCallback();
    this._listenEvents();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    if (this._hass) {
      this._hass.connection.socket.removeEventListener('message', this._onMessage);
    }
  }

  _listenEvents() {
    if (!this._hass) return;
    const conn = this._hass.connection;
    if (conn && conn.socket) {
      conn.socket.addEventListener('message', (e) => this._onMessage(e));
    }
  }

  _onMessage(e) {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'event' && data.event) {
        const { event } = data.event;
        if (event && event.event_type === 'uppercoast_doorlock_call_started') {
          this._showCallPopup = true;
          this._callActive = true;
          this._deviceName = event.data.device_name || '';
          this._displayName = event.data.display_name || '';
          this._targetIp = event.data.target_ip || '';
          this._floorLabel = event.data.floor_label || '';
          this._positionDetail = event.data.position_detail || '';
        }
        if (event && event.event_type === 'uppercoast_doorlock_call_ended') {
          this._showCallPopup = false;
          this._callActive = false;
        }
      }
    } catch (_) {}
  }

  set hass(hass) {
    this._hass = hass;
    this._listenEvents();
    this._loadState();
  }

  async _loadState() {
    if (!this._hass) return;
    const state = this._hass.states['binary_sensor.uppercoast_doorlock_call_active'];
    if (state) {
      this._callActive = state.state === 'on';
      const attrs = state.attributes || {};
      this._deviceName = attrs.device_name || '';
      this._displayName = attrs.display_name || '';
      this._targetIp = attrs.target_ip || '';
      this._floorLabel = attrs.floor_label || '';
      this._positionDetail = attrs.position_detail || '';
      if (this._callActive) {
        this._showCallPopup = true;
      }
    }
    this._fetchCameraFrame();
  }

  async _fetchCameraFrame() {
    if (!this._hass) return;
    this._loadingFrame = true;
    try {
      const resp = await this._hass.fetchWithAuth('/api/uppercoast_doorlock/frame');
      if (resp.ok) {
        const blob = await resp.blob();
        this._cameraUrl = URL.createObjectURL(blob);
      }
    } catch (_) {}
    this._loadingFrame = false;
  }

  _callService(service) {
    if (!this._hass || !this._targetIp) return;
    this._hass.callService('uppercoast_doorlock', service, {
      target_ip: this._targetIp
    });
  }

  _closePopup() {
    this._showCallPopup = false;
    this._callActive = false;
  }

  _renderDoorItem(name, floor, position, status) {
    return html`
      <div class="door-item ${status === 'offline' ? 'offline' : ''}">
        <div class="door-indicator ${status}"></div>
        <div class="door-info">
          <div class="door-name">${name}</div>
          <div class="door-location">${floor} · ${position}</div>
        </div>
      </div>
    `;
  }

  render() {
    return html`
      <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
      <div class="card">
        <div class="header">
          <div class="header-title">
            <span class="header-icon">🏠</span>
            云海湾门禁系统
          </div>
          <div class="status-badge ${this._callActive ? 'active' : ''}">
            ${this._callActive ? '呼叫中' : '待机'}
          </div>
        </div>
        <div class="door-list">
          ${this._renderDoorItem('1号机', '1层', '车库', 'online')}
          ${this._renderDoorItem('2号机', '2层', '花园', 'online')}
          ${this._renderDoorItem('3号机', '-1层', '车库', 'offline')}
          ${this._renderDoorItem('4号机', '-2层', '车库', 'offline')}
          ${this._renderDoorItem('5号机', '-1层', '电梯左侧小门左边', 'offline')}
          ${this._renderDoorItem('6号机', '-1层', '电梯右侧小门右边', 'offline')}
          ${this._renderDoorItem('7号机', '-2层', '电梯左侧小门左边', 'offline')}
          ${this._renderDoorItem('8号机', '1层', '电梯正对', 'offline')}
        </div>
      </div>

      ${this._showCallPopup ? html`
        <div class="overlay" @click=${this._closePopup}></div>
        <div class="call-popup">
          <div class="popup-header">
            <span class="popup-title">${this._displayName} 正在呼叫</span>
            <button class="popup-close" @click=${this._closePopup}>✕</button>
          </div>
          <div class="popup-video">
            ${this._cameraUrl
              ? html`<img src="${this._cameraUrl}" alt="视频" />`
              : html`<span>正在加载视频...</span>`
            }
          </div>
          <div class="popup-actions">
            <button class="popup-btn unlock" @click=${() => this._callService('unlock')}>🔓 解锁</button>
            <button class="popup-btn answer" @click=${() => this._callService('answer')}>📞 接听</button>
            <button class="popup-btn hangup" @click=${() => this._callService('hangup')}>挂断</button>
          </div>
        </div>
      ` : ''}
    `;
  }
}

customElements.define('doorlock-card', DoorlockCard);