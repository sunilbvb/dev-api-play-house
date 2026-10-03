import { apiClient } from '../api_client.js';

export class EnvironmentManager {
  constructor(app) {
    this.app = app;
    this.environments = [];
    this.activeEnvId = null;
    this.selectedModalEnvId = null;

    this.selectEl = document.getElementById('env-select');
    this.modalEl = document.getElementById('modal-env');
    this.btnManage = document.getElementById('btn-manage-env');
    this.btnCreate = document.getElementById('btn-create-env');
    this.btnSave = document.getElementById('btn-save-env');
    this.btnDelete = document.getElementById('btn-delete-env');

    this.initEvents();
  }

  initEvents() {
    this.selectEl.addEventListener('change', async (e) => {
      const id = e.target.value ? parseInt(e.target.value) : null;
      await this.setActive(id);
    });

    this.btnManage.addEventListener('click', () => this.openModal());
    this.btnCreate.addEventListener('click', () => this.createNew());
    this.btnSave.addEventListener('click', () => this.saveSelected());
    this.btnDelete.addEventListener('click', () => this.deleteSelected());

    document.querySelectorAll('[data-close="modal-env"]').forEach(btn => {
      btn.addEventListener('click', () => this.modalEl.classList.add('hidden'));
    });
  }

  async loadEnvironments() {
    try {
      this.environments = await apiClient.getEnvironments();
      this.renderDropdown();
    } catch (err) {
      this.app.showToast(`Failed loading environments: ${err.message}`, 'error');
    }
  }

  renderDropdown() {
    this.selectEl.innerHTML = '';
    const noneOpt = document.createElement('option');
    noneOpt.value = '';
    noneOpt.textContent = 'No Environment';
    this.selectEl.appendChild(noneOpt);

    let activeFound = false;
    this.environments.forEach(env => {
      const opt = document.createElement('option');
      opt.value = env.id;
      opt.textContent = env.name;
      if (env.is_active) {
        opt.selected = true;
        this.activeEnvId = env.id;
        activeFound = true;
      }
      this.selectEl.appendChild(opt);
    });

    if (!activeFound) {
      this.activeEnvId = null;
      noneOpt.selected = true;
    }
  }

  async setActive(id) {
    try {
      await apiClient.setActiveEnvironment(id);
      this.activeEnvId = id;
      this.app.showToast('Active environment updated', 'success');
      this.loadEnvironments();
    } catch (err) {
      this.app.showToast(`Failed setting active environment: ${err.message}`, 'error');
    }
  }

  openModal() {
    this.renderModalList();
    if (this.environments.length > 0) {
      this.selectModalEnv(this.activeEnvId || this.environments[0].id);
    }
    this.modalEl.classList.remove('hidden');
  }

  renderModalList() {
    const listEl = document.getElementById('env-items-list');
    listEl.innerHTML = '';
    this.environments.forEach(env => {
      const item = document.createElement('div');
      item.className = `env-list-item ${this.selectedModalEnvId === env.id ? 'active' : ''}`;
      item.textContent = env.name;
      item.addEventListener('click', () => this.selectModalEnv(env.id));
      listEl.appendChild(item);
    });
  }

  selectModalEnv(id) {
    this.selectedModalEnvId = id;
    this.renderModalList();
    const env = this.environments.find(e => e.id === id);
    if (env) {
      document.getElementById('env-edit-name').value = env.name;
      document.getElementById('env-edit-vars').value = JSON.stringify(env.variables || {}, null, 2);
    }
  }

  async createNew() {
    const name = prompt('Enter new environment name:', 'Staging');
    if (!name) return;
    try {
      const created = await apiClient.createEnvironment(name, { base_url: "https://httpbin.org" });
      await this.loadEnvironments();
      this.selectModalEnv(created.id);
      this.app.showToast(`Created environment: ${name}`, 'success');
    } catch (err) {
      this.app.showToast(`Create failed: ${err.message}`, 'error');
    }
  }

  async saveSelected() {
    if (!this.selectedModalEnvId) return;
    const name = document.getElementById('env-edit-name').value.trim();
    const rawVars = document.getElementById('env-edit-vars').value.trim();
    let varsObj = {};
    try {
      varsObj = JSON.parse(rawVars || '{}');
    } catch (e) {
      return this.app.showToast('Variables must be valid JSON', 'error');
    }

    try {
      await apiClient.updateEnvironment(this.selectedModalEnvId, name, varsObj);
      await this.loadEnvironments();
      this.renderModalList();
      this.app.showToast('Environment saved successfully', 'success');
    } catch (err) {
      this.app.showToast(`Save failed: ${err.message}`, 'error');
    }
  }

  async deleteSelected() {
    if (!this.selectedModalEnvId) return;
    if (!confirm('Are you sure you want to delete this environment?')) return;
    try {
      await apiClient.deleteEnvironment(this.selectedModalEnvId);
      await this.loadEnvironments();
      this.selectedModalEnvId = this.environments[0] ? this.environments[0].id : null;
      this.renderModalList();
      if (this.selectedModalEnvId) {
        this.selectModalEnv(this.selectedModalEnvId);
      }
      this.app.showToast('Environment deleted', 'success');
    } catch (err) {
      this.app.showToast(`Delete failed: ${err.message}`, 'error');
    }
  }
}
