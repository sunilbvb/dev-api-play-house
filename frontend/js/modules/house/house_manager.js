import { apiClient } from '../api_client.js';

export class HouseManager {
  constructor(app) {
    this.app = app;
    this.modalEl = document.getElementById('modal-auto-house');
    this.btnOpen = document.getElementById('btn-open-auto-house');
    this.btnBuild = document.getElementById('btn-do-build-house');

    this.rawTextInput = document.getElementById('house-raw-apis');
    this.workspacePathInput = document.getElementById('house-workspace-path');
    this.houseNameInput = document.getElementById('house-name');
    this.themeSelect = document.getElementById('house-theme-select');

    // Vitals HUD elements
    this.hudEl = document.getElementById('house-vitals-hud');
    this.hpBarFill = document.getElementById('hud-hp-fill');
    this.hpText = document.getElementById('hud-hp-text');
    this.xpText = document.getElementById('hud-xp-text');
    this.latencyText = document.getElementById('hud-latency-text');
    this.bossCard = document.getElementById('hud-boss-card');

    this.initEvents();
  }

  initEvents() {
    if (this.btnOpen) {
      this.btnOpen.addEventListener('click', () => {
        this.modalEl.classList.remove('hidden');
      });
    }

    document.querySelectorAll('[data-close="modal-auto-house"]').forEach(btn => {
      btn.addEventListener('click', () => this.modalEl.classList.add('hidden'));
    });

    if (this.btnBuild) {
      this.btnBuild.addEventListener('click', () => this.buildGameHouse());
    }
  }

  async buildGameHouse() {
    const rawText = this.rawTextInput.value.trim();
    const workspacePath = this.workspacePathInput.value.trim();
    const houseName = this.houseNameInput.value.trim() || 'Arcade Game House';
    const themeKey = this.themeSelect.value;

    if (!rawText && !workspacePath) {
      return this.app.showToast('Please provide a list of API URLs or a workspace path', 'error');
    }

    try {
      this.app.showToast('Auto-Architecting Game House with Quests & Boss...', 'info');
      const result = await apiClient.autoBuildHouse({
        raw_text: rawText,
        workspace_path: workspacePath,
        house_name: houseName,
        theme_key: themeKey
      });

      this.app.showToast(`🏰 Created "${result.house_name}" with ${result.stats.total_quests} Quests!`, 'success');
      this.modalEl.classList.add('hidden');
      this.rawTextInput.value = '';
      this.workspacePathInput.value = '';

      // Reload explorer and select new game house
      await this.app.explorer.loadData();
      if (result.collection_id) {
        this.app.explorer.selectRequest(result.ordered_sequence[0].id);
        // Switch to workflow quest tab
        document.querySelector('.nav-tab[data-tab="workflow"]').click();
        await this.refreshVitals(result.collection_id);
      }
    } catch (err) {
      this.app.showToast(`Auto-build failed: ${err.message}`, 'error');
    }
  }

  async refreshVitals(collectionId) {
    if (!collectionId) return;
    try {
      const vitals = await apiClient.getHouseVitals(collectionId);
      if (this.hudEl) {
        this.hudEl.classList.remove('hidden');
        this.hpText.textContent = `${vitals.house_hp}%`;
        this.hpBarFill.style.width = `${vitals.house_hp}%`;
        
        // Color code HP
        if (vitals.house_hp > 70) {
          this.hpBarFill.style.background = 'var(--accent-green)';
        } else if (vitals.house_hp > 30) {
          this.hpBarFill.style.background = 'var(--accent-orange)';
        } else {
          this.hpBarFill.style.background = 'var(--accent-red)';
        }

        this.xpText.textContent = `${vitals.xp_earned} XP`;
        this.latencyText.textContent = `${vitals.avg_latency_ms} ms`;
        
        if (this.bossCard) {
          if (vitals.boss_defeated) {
            this.bossCard.className = 'boss-badge boss-defeated';
            this.bossCard.innerHTML = '👑 RAID BOSS DEFEATED!';
          } else {
            this.bossCard.className = 'boss-badge boss-alive';
            this.bossCard.innerHTML = '👾 RAID BOSS READY';
          }
        }
      }
    } catch (err) {
      console.warn('Could not fetch vitals:', err);
    }
  }
}
