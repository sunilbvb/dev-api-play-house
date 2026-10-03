import { EnvironmentManager } from './modules/env/env_manager.js';
import { Explorer } from './modules/explorer/explorer.js';
import { Studio } from './modules/studio/studio.js';
import { WorkflowManager } from './modules/workflow/workflow.js';
import { Importer } from './modules/importer/importer.js';
import { Exporter } from './modules/exporter/exporter.js';
import { HouseManager } from './modules/house/house_manager.js';
import { TrophyManager } from './modules/trophies/trophy_manager.js';
import { CoopManager } from './modules/coop/coop_manager.js';
import { ReplayManager } from './modules/replay/replay_manager.js';
import { DocManager } from './modules/docs/doc_manager.js';
import { AdvisorManager } from './modules/advisor/advisor_manager.js';
import { RealtimeStudio } from './modules/realtime/realtime_studio.js';

class App {
  constructor() {
    this.toastContainer = document.getElementById('toast-container');
    
    // Submodules
    this.envManager = new EnvironmentManager(this);
    this.explorer = new Explorer(this);
    this.studio = new Studio(this);
    this.workflow = new WorkflowManager(this);
    this.importer = new Importer(this);
    this.exporter = new Exporter(this);
    this.house = new HouseManager(this);
    this.trophies = new TrophyManager(this);
    this.coop = new CoopManager(this);
    this.replay = new ReplayManager(this);
    this.docs = new DocManager(this);
    this.advisor = new AdvisorManager(this);
    this.realtime = new RealtimeStudio(this);

    this.initNavigation();
  }

  async init() {
    await this.envManager.loadEnvironments();
    await this.explorer.loadData();
    console.log("🎮 Dev API Play House initialized!");
  }

  initNavigation() {
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

        tab.classList.add('active');
        const targetTab = tab.dataset.tab;
        document.getElementById(`tab-${targetTab}`).classList.add('active');

        if (targetTab === 'workflow') {
          this.workflow.analyzeCurrentWorkflow();
        }
      });
    });
  }

  onRequestSelected(req) {
    this.studio.loadRequest(req);
  }

  onCollectionSelected(colId) {
    this.house.refreshVitals(colId);
    if (document.getElementById('tab-workflow').classList.contains('active')) {
      this.workflow.analyzeCurrentWorkflow();
    }
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    this.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// Bootstrap
window.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
