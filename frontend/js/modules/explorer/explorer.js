import { apiClient } from '../api_client.js';

export class Explorer {
  constructor(app) {
    this.app = app;
    this.collections = [];
    this.requests = [];
    this.activeRequestId = null;
    this.activeCollectionId = null;

    this.containerEl = document.getElementById('collections-tree');
    this.searchInput = document.getElementById('api-search');
    this.btnNewCol = document.getElementById('btn-new-collection');
    this.btnNewReq = document.getElementById('btn-new-request');

    this.initEvents();
  }

  initEvents() {
    this.searchInput.addEventListener('input', () => this.render());
    this.btnNewCol.addEventListener('click', () => this.createCollection());
    this.btnNewReq.addEventListener('click', () => this.createRequest());
  }

  async loadData() {
    try {
      this.collections = await apiClient.getCollections();
      this.requests = await apiClient.getRequests();
      this.render();

      // Auto-select first request if none selected
      if (!this.activeRequestId && this.requests.length > 0) {
        this.selectRequest(this.requests[0].id);
      }
    } catch (err) {
      this.app.showToast(`Failed loading collections: ${err.message}`, 'error');
    }
  }

  render() {
    const query = this.searchInput.value.trim().toLowerCase();
    this.containerEl.innerHTML = '';

    if (this.collections.length === 0) {
      this.containerEl.innerHTML = `<p style="padding:10px; color:var(--text-muted); font-size:12px;">No collections found. Click "+ Col" or "Import" to get started.</p>`;
      return;
    }

    this.collections.forEach(col => {
      const colReqs = this.requests.filter(r => r.collection_id === col.id);
      const filteredReqs = colReqs.filter(r => {
        if (!query) return true;
        return (r.name && r.name.toLowerCase().includes(query)) ||
               (r.url && r.url.toLowerCase().includes(query)) ||
               (r.method && r.method.toLowerCase().includes(query));
      });

      if (query && filteredReqs.length === 0 && !col.name.toLowerCase().includes(query)) {
        return;
      }

      const card = document.createElement('div');
      card.className = 'col-card';

      const header = document.createElement('div');
      header.className = 'col-header';
      header.innerHTML = `
        <span>📁 ${col.name}</span>
        <span class="col-count">${colReqs.length}</span>
      `;
      header.addEventListener('click', () => {
        this.activeCollectionId = col.id;
        this.app.onCollectionSelected(col.id);
      });
      card.appendChild(header);

      const itemsContainer = document.createElement('div');
      itemsContainer.className = 'col-items';

      filteredReqs.forEach(req => {
        const item = document.createElement('div');
        item.className = `req-item ${this.activeRequestId === req.id ? 'active' : ''}`;
        item.innerHTML = `
          <span class="badge-method ${req.method}">${req.method}</span>
          <span class="req-name" title="${req.url}">${req.name || req.url}</span>
        `;
        item.addEventListener('click', () => this.selectRequest(req.id));
        itemsContainer.appendChild(item);
      });

      card.appendChild(itemsContainer);
      this.containerEl.appendChild(card);
    });
  }

  selectRequest(id) {
    this.activeRequestId = id;
    const req = this.requests.find(r => r.id === id);
    if (req) {
      this.activeCollectionId = req.collection_id;
      this.render();
      this.app.onRequestSelected(req);
    }
  }

  async createCollection() {
    const name = prompt('Enter new Collection Name:', 'Game Matchmaking APIs');
    if (!name) return;
    try {
      await apiClient.createCollection(name);
      await this.loadData();
      this.app.showToast(`Collection "${name}" created`, 'success');
    } catch (err) {
      this.app.showToast(`Failed: ${err.message}`, 'error');
    }
  }

  async createRequest() {
    if (this.collections.length === 0) {
      return this.app.showToast('Please create a collection first', 'error');
    }
    const colId = this.activeCollectionId || this.collections[0].id;
    const name = prompt('Enter API Name:', 'New API Endpoint');
    if (!name) return;

    try {
      const created = await apiClient.createRequest({
        collection_id: colId,
        name: name,
        method: 'GET',
        url: '{{base_url}}/get',
        headers: {},
        body: '',
        body_type: 'none',
        extracts: []
      });
      await this.loadData();
      this.selectRequest(created.id);
      this.app.showToast(`API "${name}" added`, 'success');
    } catch (err) {
      this.app.showToast(`Failed: ${err.message}`, 'error');
    }
  }
}
