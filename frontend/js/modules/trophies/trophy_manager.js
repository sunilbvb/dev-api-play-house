import { apiClient } from '../api_client.js';

export class TrophyManager {
  constructor(app) {
    this.app = app;
    this.modalEl = document.getElementById('modal-trophies');
    this.btnOpen = document.getElementById('btn-open-trophies');
    this.listEl = document.getElementById('trophies-list');

    this.initEvents();
  }

  initEvents() {
    if (this.btnOpen) {
      this.btnOpen.addEventListener('click', () => this.openModal());
    }

    document.querySelectorAll('[data-close="modal-trophies"]').forEach(btn => {
      btn.addEventListener('click', () => this.modalEl.classList.add('hidden'));
    });
  }

  async openModal() {
    this.modalEl.classList.remove('hidden');
    await this.loadTrophies();
  }

  async loadTrophies() {
    try {
      const trophies = await apiClient.getTrophies();
      this.render(trophies);
    } catch (err) {
      console.warn('Could not load trophies:', err);
    }
  }

  render(trophies) {
    this.listEl.innerHTML = '';
    trophies.forEach(t => {
      const card = document.createElement('div');
      card.className = `trophy-card ${t.unlocked ? 'unlocked' : 'locked'}`;
      card.innerHTML = `
        <div class="trophy-icon">${t.icon}</div>
        <div class="trophy-details">
          <div class="trophy-title">
            <span>${t.title}</span>
            <span class="trophy-xp">+${t.xp} XP</span>
          </div>
          <div class="trophy-desc">${t.description}</div>
          <div class="trophy-badge-status">${t.unlocked ? '🏆 UNLOCKED' : '🔒 LOCKED'}</div>
        </div>
      `;
      this.listEl.appendChild(card);
    });
  }

  notifyNewTrophies(newTrophies) {
    if (!newTrophies || newTrophies.length === 0) return;
    newTrophies.forEach(t => {
      this.app.showToast(`🏆 UNLOCKED ACHIEVEMENT: ${t.icon} ${t.title}! (+${t.xp} XP)`, 'success');
    });
  }
}
