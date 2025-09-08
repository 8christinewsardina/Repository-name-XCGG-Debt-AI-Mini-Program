Page({
  data: { apiBase: '' },
  onLoad() {
    const stored = wx.getStorageSync('API_BASE');
    const token = wx.getStorageSync('API_TOKEN');
    this.setData({ apiBase: stored || 'http://127.0.0.1:8000', apiToken: token || '' });
  },
  onInput(e) {
    this.setData({ apiBase: e.detail.value });
  },
  onTokenInput(e) {
    this.setData({ apiToken: e.detail.value });
  },
  save() {
    wx.setStorageSync('API_BASE', this.data.apiBase);
    wx.setStorageSync('API_TOKEN', this.data.apiToken || '');
    wx.showToast({ title: '已保存', icon: 'success' });
  }
});
