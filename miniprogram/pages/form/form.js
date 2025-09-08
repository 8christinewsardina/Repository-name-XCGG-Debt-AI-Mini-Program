// pages/form/form.js
Page({

  /**
   * 页面的初始数据
   */
  data: {

  },

  /**
   * 表单提交事件
   */
  submitForm: function(e) {
    const formData = e.detail.value;
    console.log('用户提交的表单数据：', formData);

    // 简单的数据校验
    if (!formData.assets || !formData.liabilities || !formData.income || !formData.expenses) {
      wx.showToast({
        title: '请填写所有项目',
        icon: 'none'
      });
      return;
    }

    const config = require('../../config.js');
    const url = `${config.API_BASE}/api/v1/reports`;

    wx.showLoading({ title: 'AI正在分析中...' });

    const token = config.API_TOKEN || '';

    const send = (attempt = 1) => {
      wx.request({
        url: url,
        method: 'POST',
        header: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        data: {
          assets: Number(formData.assets),
          liabilities: Number(formData.liabilities),
          income: Number(formData.income),
          expenses: Number(formData.expenses),
          notes: formData.notes || ''
        },
        success(res) {
          wx.hideLoading();
          if (res.statusCode === 200) {
            const analysis = res.data.analysis || {};
            wx.showModal({
              title: '分析结果',
              content: `负债率: ${res.data.debt_ratio}\n概述: ${analysis.overview || ''}\n建议: ${(analysis.recommendations||[]).join('；')}`,
              showCancel: false
            });
          } else {
            wx.showToast({ title: `服务错误 ${res.statusCode}`, icon: 'none' });
          }
        },
        fail() {
          if (attempt < 3) {
            // 简单重试
            setTimeout(() => send(attempt + 1), 1000 * attempt);
          } else {
            wx.hideLoading();
            wx.showToast({ title: '网络请求失败', icon: 'none' });
          }
        }
      });
    };

    send();
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {

  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {

  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {

  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {

  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {

  }
})