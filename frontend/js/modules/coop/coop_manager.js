import { apiClient } from '../api_client.js';

export class CoopManager {
  constructor(app) {
    this.app = app;
    this.lastEventId = 0;
    this.feedEl = document.getElementById('coop-live-feed');
    this.btnPing = document.getElementById('btn-coop-ping');

    this.initEvents();
    this.startPolling();
  }

  initEvents() {
    if (this.btnPing) {
      this.btnPing.addEventListener('click', async () => {
        try {
          await apiClient.postCoopEvent('Hero_Dev', 'Sent party ping in lobby!');
          this.fetchEvents();
        } catch (e) {}
      });
    }
  }

  startPolling() {
    this.fetchEvents();
    setInterval(() => this.fetchEvents(), 4000);
  }

  async fetchEvents() {
    if (!this.feedEl) return;
    try {
      const events = await apiClient.getCoopEvents(this.lastEventId);
      if (events.length > 0) {
        events.forEach(e => {
          this.lastEventId = Math.max(this.lastEventId, e.id);
          const item = document.createElement('div');
          item.className = 'coop-event-pill';
          item.innerHTML = `<span class="coop-time">[${e.timestamp}]</span> <strong>${e.actor}</strong>: ${e.message}`;
          this.feedEl.prepend(item);
          // Keep max 5 visible in ticker
          if (this.feedEl.children.length > 5) {
            this.feedEl.lastElementChild.remove();
          }
        });
      }
    } catch (e) {}
  }
}
