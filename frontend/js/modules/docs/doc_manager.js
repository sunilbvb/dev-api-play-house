import { apiClient } from '../api_client.js';

export class DocManager {
  constructor(app) {
    this.app = app;
    this.btnGenerate = document.getElementById('btn-auto-generate-doc');
    this.docEditor = document.getElementById('api-doc-markdown');
    this.btnCopyDoc = document.getElementById('btn-copy-doc');
    this.docStatus = document.getElementById('doc-status-badge');

    this.initEvents();
  }

  initEvents() {
    if (this.btnGenerate) {
      this.btnGenerate.addEventListener('click', () => this.generateDocs());
    }

    if (this.btnCopyDoc) {
      this.btnCopyDoc.addEventListener('click', () => {
        if (!this.docEditor.value) return;
        navigator.clipboard.writeText(this.docEditor.value).then(() => {
          this.app.showToast('Documentation copied to clipboard (Markdown)', 'success');
        });
      });
    }
  }

  loadDocumentation(docText) {
    if (this.docEditor) {
      this.docEditor.value = docText || '';
      if (this.docStatus) {
        if (docText && docText.trim().length > 0) {
          this.docStatus.className = 'status-badge status-2xx';
          this.docStatus.textContent = 'Documented';
        } else {
          this.docStatus.className = 'status-badge status-idle';
          this.docStatus.textContent = 'Undocumented';
        }
      }
    }
  }

  async generateDocs() {
    const currentReq = this.app.studio.getFormData();
    if (!currentReq || !currentReq.url) {
      return this.app.showToast('Select an API with a valid URL to generate docs', 'error');
    }

    if (this.docStatus) {
      this.docStatus.textContent = 'Generating...';
    }

    try {
      this.app.showToast('Analyzing API structure & generating docs...', 'info');
      const res = await apiClient.generateApiDocs({
        request_id: currentReq.id,
        request: currentReq
      });

      this.docEditor.value = res.documentation || '';
      if (this.docStatus) {
        this.docStatus.className = 'status-badge status-2xx';
        this.docStatus.textContent = 'Documented';
      }
      this.app.showToast('Comprehensive API documentation auto-generated!', 'success');
    } catch (err) {
      if (this.docStatus) {
        this.docStatus.className = 'status-badge status-5xx';
        this.docStatus.textContent = 'Failed';
      }
      this.app.showToast(`Doc generation failed: ${err.message}`, 'error');
    }
  }
}
