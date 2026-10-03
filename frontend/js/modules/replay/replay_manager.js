import { apiClient } from '../api_client.js';

export class ReplayManager {
  constructor(app) {
    this.app = app;
    this.frames = [];
    this.currentFrameIdx = 0;

    this.containerEl = document.getElementById('replay-scrubber-bar');
    this.scrubberInput = document.getElementById('replay-scrubber-input');
    this.btnExportTape = document.getElementById('btn-export-replay-tape');
    this.frameInfoEl = document.getElementById('replay-frame-info');

    this.initEvents();
  }

  initEvents() {
    if (this.scrubberInput) {
      this.scrubberInput.addEventListener('input', (e) => {
        const idx = parseInt(e.target.value);
        this.previewFrame(idx);
      });
    }

    if (this.btnExportTape) {
      this.btnExportTape.addEventListener('click', async () => {
        try {
          const res = await apiClient.exportReplayTape();
          const blob = new Blob([res.tape], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `playhouse_session_${Date.now()}.json`;
          a.click();
          this.app.showToast('Replay session tape exported', 'success');
        } catch (err) {
          this.app.showToast('Export tape failed', 'error');
        }
      });
    }
  }

  async loadSessionFrames() {
    try {
      this.frames = await apiClient.getReplayFrames();
      if (this.containerEl && this.frames.length > 0) {
        this.containerEl.classList.remove('hidden');
        this.scrubberInput.max = this.frames.length - 1;
        this.scrubberInput.value = this.frames.length - 1;
        this.previewFrame(this.frames.length - 1);
      }
    } catch (e) {}
  }

  previewFrame(idx) {
    const frame = this.frames[idx];
    if (!frame) return;
    this.currentFrameIdx = idx;
    if (this.frameInfoEl) {
      this.frameInfoEl.textContent = `Frame ${idx + 1}/${this.frames.length} (${frame.time_str}) - ${frame.request.name || frame.request.url}`;
    }
  }
}
