import { apiClient } from '../api_client.js';

export class Exporter {
  constructor(app) {
    this.app = app;
    this.modalEl = document.getElementById('modal-export');
    this.btnOpen = document.getElementById('btn-open-export');
    this.formatSelect = document.getElementById('export-format-select');
    this.resultText = document.getElementById('export-result-text');
    this.btnCopyModal = document.getElementById('btn-copy-export-modal');

    this.initEvents();
  }

  initEvents() {
    this.btnOpen.addEventListener('click', () => this.openModal());
    this.formatSelect.addEventListener('change', () => this.generateExport());
    document.querySelectorAll('input[name="export_scope"]').forEach(r => {
      r.addEventListener('change', () => this.generateExport());
    });
    this.btnCopyModal.addEventListener('click', () => {
      if (!this.resultText.value) return;
      navigator.clipboard.writeText(this.resultText.value).then(() => {
        this.app.showToast('Export content copied to clipboard!', 'success');
      });
    });

    document.querySelectorAll('[data-close="modal-export"]').forEach(btn => {
      btn.addEventListener('click', () => this.modalEl.classList.add('hidden'));
    });
  }

  openModal() {
    this.modalEl.classList.remove('hidden');
    this.generateExport();
  }

  async generateExport() {
    const format = this.formatSelect.value;
    const scope = document.querySelector('input[name="export_scope"]:checked').value;

    let targetRequests = [];
    let collectionName = 'Exported APIs';

    if (scope === 'current') {
      const currentReq = this.app.studio.getFormData();
      if (!currentReq.url) {
        this.resultText.value = '// No active API request to export';
        return;
      }
      targetRequests = [currentReq];
    } else {
      // Export whole active collection
      const colId = this.app.explorer.activeCollectionId;
      const col = this.app.explorer.collections.find(c => c.id === colId);
      if (col) collectionName = col.name;
      targetRequests = this.app.explorer.requests.filter(r => r.collection_id === colId);
      if (targetRequests.length === 0) {
        this.resultText.value = '// No APIs found in selected collection';
        return;
      }
    }

    try {
      const res = await apiClient.exportApis(format, targetRequests, collectionName);
      this.resultText.value = res.content || '';
    } catch (err) {
      this.resultText.value = `Export error: ${err.message}`;
    }
  }
}
