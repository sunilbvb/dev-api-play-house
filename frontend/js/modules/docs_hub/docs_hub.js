import { apiClient } from '../api_client.js';

export class DocsHubManager {
  constructor(app) {
    this.app = app;
    this.currentDoc = 'readme';
    this.currentSection = 'documentation';
    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // Sub-nav inside Docs tab
    document.querySelectorAll('.docs-nav-item').forEach(item => {
      item.addEventListener('click', () => {
        const target = item.dataset.docsSection;
        this.switchSection(target);
      });
    });

    // Doc pills inside live_docs section
    document.querySelectorAll('.doc-pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.doc-pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentDoc = btn.dataset.docFile;
        this.loadLiveDoc(this.currentDoc);
      });
    });

    // Copy live doc button
    const btnCopyDoc = document.getElementById('btn-copy-live-doc');
    if (btnCopyDoc) {
      btnCopyDoc.addEventListener('click', () => {
        const text = document.getElementById('live-doc-raw')?.textContent || '';
        navigator.clipboard.writeText(text);
        this.app.showToast('Copied document markdown to clipboard!', 'success');
      });
    }

    // Quick copy command buttons
    document.querySelectorAll('.btn-quick-copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const cmd = btn.dataset.copyCmd;
        if (cmd) {
          navigator.clipboard.writeText(cmd);
          this.app.showToast(`Copied: ${cmd}`, 'success');
        }
      });
    });
  }

  switchSection(sectionId) {
    if (!sectionId) sectionId = 'documentation';

    // Highlight sidebar nav item
    document.querySelectorAll('.docs-nav-item').forEach(i => {
      if (i.dataset.docsSection === sectionId) {
        i.classList.add('active');
      } else {
        i.classList.remove('active');
      }
    });

    // Toggle content panels
    document.querySelectorAll('.docs-section-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById(`docs-sec-${sectionId}`);
    if (panel) {
      panel.classList.add('active');
      const container = document.querySelector('.docs-content-container');
      if (container) container.scrollTop = 0;
    }

    this.currentSection = sectionId;

    if (sectionId === 'live_docs') {
      this.loadLiveDoc(this.currentDoc);
    }
  }

  async loadLiveDoc(docName) {
    const rawEl = document.getElementById('live-doc-raw');
    const titleEl = document.getElementById('live-doc-title');
    const pathEl = document.getElementById('live-doc-path');

    if (!rawEl) return;
    rawEl.textContent = 'Loading document...';

    try {
      const res = await apiClient.getDocContent(docName);
      if (titleEl) titleEl.textContent = `${docName.toUpperCase()}.md`;
      if (pathEl) pathEl.textContent = res.path || '';
      rawEl.textContent = res.content || '// Empty document';
    } catch (err) {
      rawEl.textContent = `Error loading document: ${err.message}`;
      this.app.showToast(`Failed to load ${docName}: ${err.message}`, 'error');
    }
  }
}
