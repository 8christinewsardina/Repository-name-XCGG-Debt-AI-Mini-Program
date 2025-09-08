// 小程序全局配置
// 请在生产环境将 API_BASE 修改为部署后的域名（https）并在微信后台登记合法域名
// 小程序全局配置
const DEFAULT = { API_BASE: 'http://127.0.0.1:8000', API_TOKEN: '' };

try {
  // 在微信小程序环境中优先读取本地存储
  const base = (typeof wx !== 'undefined' && wx.getStorageSync) ? wx.getStorageSync('API_BASE') : null;
  const token = (typeof wx !== 'undefined' && wx.getStorageSync) ? wx.getStorageSync('API_TOKEN') : null;
  module.exports = { API_BASE: base || DEFAULT.API_BASE, API_TOKEN: token || DEFAULT.API_TOKEN };
} catch (e) {
  module.exports = DEFAULT;
}
