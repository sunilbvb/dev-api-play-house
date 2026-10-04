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
import { DocsHubManager } from './modules/docs_hub/docs_hub.js';

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
    this.docsHub = new DocsHubManager(this);

    this.initNavigation();
  }

  async init() {
    await this.envManager.loadEnvironments();
    await this.explorer.loadData();
    console.log("🎮 Dev API Play House initialized!");
  }

  initNavigation() {
    this.currentPlayTab = 'studio';
    const subbar = document.getElementById('playground-subbar');

    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

        tab.classList.add('active');
        const targetTab = tab.dataset.tab;
        const targetSec = tab.dataset.docsSec;

        if (targetTab === 'playground') {
          if (subbar) subbar.classList.remove('hidden');
          const panel = document.getElementById(`tab-${this.currentPlayTab}`);
          if (panel) panel.classList.add('active');
          if (this.currentPlayTab === 'workflow') {
            this.workflow.analyzeCurrentWorkflow();
          }
        } else if (targetTab === 'docs') {
          if (subbar) subbar.classList.add('hidden');
          document.getElementById('tab-docs').classList.add('active');
          this.docsHub.switchSection(targetSec || 'documentation');
        } else {
          if (subbar) subbar.classList.remove('hidden');
          const panel = document.getElementById(`tab-${targetTab}`);
          if (panel) panel.classList.add('active');
        }
      });
    });

    // Sub-nav for Playground modes (Studio, Workflow, Real-Time)
    document.querySelectorAll('.subnav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.subnav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const playTab = btn.dataset.playTab;
        this.currentPlayTab = playTab;

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        const panel = document.getElementById(`tab-${playTab}`);
        if (panel) panel.classList.add('active');

        // Ensure Playground in topbar is active
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        const playNav = document.querySelector('.nav-tab[data-tab="playground"]');
        if (playNav) playNav.classList.add('active');

        if (subbar) subbar.classList.remove('hidden');

        if (playTab === 'workflow') {
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
