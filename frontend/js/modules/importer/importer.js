import { apiClient } from '../api_client.js';

export class Importer {
  constructor(app) {
    this.app = app;
    this.modalEl = document.getElementById('modal-import');
    this.btnOpen = document.getElementById('btn-open-import');
    this.btnProcess = document.getElementById('btn-do-import');
    this.contentInput = document.getElementById('import-content');
    this.colNameInput = document.getElementById('import-col-name');
    this.activeType = 'curl';

    this.initEvents();
  }

  initEvents() {
    this.btnOpen.addEventListener('click', () => {
      this.modalEl.classList.remove('hidden');
    });

    document.querySelectorAll('[data-close="modal-import"]').forEach(btn => {
      btn.addEventListener('click', () => this.modalEl.classList.add('hidden'));
    });

    document.querySelectorAll('.import-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.import-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.activeType = tab.dataset.imptype;

        // Set helpful placeholder
        if (this.activeType === 'curl') {
          this.contentInput.placeholder = "curl -X POST https://api.game.io/v1/auth -H 'Content-Type: application/json' -d '{\"user\":\"neo\"}'";
        } else if (this.activeType === 'postman') {
          this.contentInput.placeholder = 'Paste Postman Collection (v2.1) JSON here...';
        } else if (this.activeType === 'http') {
          this.contentInput.placeholder = "### Login Request\nPOST https://api.game.io/v1/login\nContent-Type: application/json\n\n{\"user\":\"neo\"}\n\n### Get Stats\nGET https://api.game.io/v1/stats";
        } else if (this.activeType === 'markdown') {
          this.contentInput.placeholder = "# Game API Docs\n\nRun this cURL:\n```bash\ncurl -X GET https://api.game.io/characters\n```";
        } else if (this.activeType === 'openapi') {
          this.contentInput.placeholder = "Paste OpenAPI 3.0 / 3.1 or Swagger 2.0 (JSON) specification here...";
        }
      });
    });

    this.btnProcess.addEventListener('click', () => this.processImport());
  }

  async processImport() {
    const content = this.contentInput.value.trim();
    const colName = this.colNameInput.value.trim() || 'Imported APIs';

    if (!content) {
      return this.app.showToast('Please paste content to import', 'error');
    }

    try {
      const res = await apiClient.importApis(this.activeType, content, colName);
      if (res.status === 'imported_environment') {
        this.app.showToast(`Imported Postman Environment: ${res.name}`, 'success');
        await this.app.envManager.loadEnvironments();
      } else {
        this.app.showToast(`Imported ${res.imported_count} APIs into "${res.collection_name}"!`, 'success');
        await this.app.explorer.loadData();
      }
      this.modalEl.classList.add('hidden');
      this.contentInput.value = '';
    } catch (err) {
      this.app.showToast(`Import failed: ${err.message}`, 'error');
    }
  }
}
