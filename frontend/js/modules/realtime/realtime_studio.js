export class RealtimeStudio {
  constructor(app) {
    this.app = app;
    this.activeSocket = null;
    this.activeEventSource = null;
    this.connectionType = 'ws'; // 'ws' | 'sse'

    // Elements
    this.urlInput = document.getElementById('rt-url-input');
    this.typeSelect = document.getElementById('rt-type-select');
    this.btnConnect = document.getElementById('btn-rt-connect');
    this.btnDisconnect = document.getElementById('btn-rt-disconnect');
    this.btnSend = document.getElementById('btn-rt-send');
    this.btnPing = document.getElementById('btn-rt-ping');
    this.btnClear = document.getElementById('btn-rt-clear');
    this.statusBadge = document.getElementById('rt-status-badge');
    this.logContainer = document.getElementById('rt-messages-log');
    this.payloadInput = document.getElementById('rt-payload-input');

    this.initEvents();
  }

  initEvents() {
    if (this.btnConnect) {
      this.btnConnect.addEventListener('click', () => this.connect());
    }
    if (this.btnDisconnect) {
      this.btnDisconnect.addEventListener('click', () => this.disconnect());
    }
    if (this.btnSend) {
      this.btnSend.addEventListener('click', () => this.sendMessage());
    }
    if (this.btnPing) {
      this.btnPing.addEventListener('click', () => {
        this.payloadInput.value = JSON.stringify({ type: "ping", timestamp: Date.now() }, null, 2);
        this.sendMessage();
      });
    }
    if (this.btnClear) {
      this.btnClear.addEventListener('click', () => {
        if (this.logContainer) this.logContainer.innerHTML = '';
      });
    }
  }

  connect() {
    const url = this.urlInput.value.trim();
    if (!url) {
      return this.app.showToast('Please specify a WebSocket or SSE URL', 'error');
    }

    this.disconnect();
    this.connectionType = this.typeSelect.value;
    this.updateStatus('connecting', 'Connecting...');

    if (this.connectionType === 'ws') {
      try {
        this.activeSocket = new WebSocket(url);

        this.activeSocket.onopen = () => {
          this.updateStatus('connected', 'WS Connected');
          this.logMessage('system', `Connected to WebSocket: ${url}`);
          this.btnConnect.classList.add('hidden');
          this.btnDisconnect.classList.remove('hidden');
        };

        this.activeSocket.onmessage = (event) => {
          this.logMessage('in', event.data);
        };

        this.activeSocket.onerror = (err) => {
          this.logMessage('error', `WebSocket Error: ${err.message || 'Connection failed'}`);
          this.updateStatus('error', 'WS Error');
        };

        this.activeSocket.onclose = (event) => {
          this.updateStatus('disconnected', 'Disconnected');
          this.logMessage('system', `WebSocket Closed (code: ${event.code})`);
          this.btnConnect.classList.remove('hidden');
          this.btnDisconnect.classList.add('hidden');
        };
      } catch (e) {
        this.updateStatus('error', 'Init Failed');
        this.logMessage('error', `Connection exception: ${e.message}`);
      }
    } else {
      // Server-Sent Events (SSE)
      try {
        this.activeEventSource = new EventSource(url);

        this.activeEventSource.onopen = () => {
          this.updateStatus('connected', 'SSE Connected');
          this.logMessage('system', `Listening to SSE stream: ${url}`);
          this.btnConnect.classList.add('hidden');
          this.btnDisconnect.classList.remove('hidden');
        };

        this.activeEventSource.onmessage = (event) => {
          this.logMessage('in', event.data);
        };

        this.activeEventSource.onerror = () => {
          this.updateStatus('error', 'SSE Error');
          this.logMessage('error', 'SSE connection disconnected or errored');
        };
      } catch (e) {
        this.updateStatus('error', 'Init Failed');
        this.logMessage('error', `SSE exception: ${e.message}`);
      }
    }
  }

  disconnect() {
    if (this.activeSocket) {
      this.activeSocket.close();
      this.activeSocket = null;
    }
    if (this.activeEventSource) {
      this.activeEventSource.close();
      this.activeEventSource = null;
    }
    this.updateStatus('disconnected', 'Disconnected');
    if (this.btnConnect && this.btnDisconnect) {
      this.btnConnect.classList.remove('hidden');
      this.btnDisconnect.classList.add('hidden');
    }
  }

  sendMessage() {
    const text = this.payloadInput.value.trim();
    if (!text) return;

    if (!this.activeSocket || this.activeSocket.readyState !== WebSocket.OPEN) {
      return this.app.showToast('WebSocket is not connected', 'error');
    }

    try {
      this.activeSocket.send(text);
      this.logMessage('out', text);
    } catch (e) {
      this.app.showToast(`Send failed: ${e.message}`, 'error');
    }
  }

  logMessage(direction, data) {
    if (!this.logContainer) return;
    const time = new Date().toLocaleTimeString();
    const item = document.createElement('div');
    item.className = `rt-msg-item rt-msg-${direction}`;

    let label = 'SYS';
    if (direction === 'in') label = 'IN ⬇';
    if (direction === 'out') label = 'OUT ⬆';
    if (direction === 'error') label = 'ERR ⚠️';

    let formattedData = data;
    try {
      if (typeof data === 'string' && (data.startsWith('{') || data.startsWith('['))) {
        formattedData = JSON.stringify(JSON.parse(data), null, 2);
      }
    } catch (e) {}

    item.innerHTML = `
      <div class="rt-msg-meta">
        <span class="rt-msg-badge">${label}</span>
        <span class="rt-msg-time">${time}</span>
      </div>
      <pre class="rt-msg-body"><code>${formattedData}</code></pre>
    `;

    this.logContainer.appendChild(item);
    this.logContainer.scrollTop = this.logContainer.scrollHeight;
  }

  updateStatus(state, label) {
    if (!this.statusBadge) return;
    this.statusBadge.textContent = label;
    if (state === 'connected') {
      this.statusBadge.className = 'status-badge status-2xx';
    } else if (state === 'connecting') {
      this.statusBadge.className = 'status-badge status-idle';
    } else if (state === 'error') {
      this.statusBadge.className = 'status-badge status-5xx';
    } else {
      this.statusBadge.className = 'status-badge status-idle';
    }
  }
}
