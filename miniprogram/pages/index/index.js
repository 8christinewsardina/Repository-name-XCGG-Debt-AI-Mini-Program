// pages/index/index.js
Page({
  /**
   * 页面的初始数据
   */
  data: {
    appName: 'AI 财务顾问'
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad: function (options) {
    console.log('首页加载完成');
  },

  /**
   * "开始分析"按钮的点击事件
   */
  startAnalysis: function () {
    console.log('按钮被点击，准备跳转到form页面...');
    wx.navigateTo({
      url: '../form/form'
    });
  },

  openSettings: function () {
    wx.navigateTo({ url: '../settings/settings' });
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady: function () {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow: function () {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage: function () {
    return {
      title: '您的专属AI财务顾问，为您提供专业分析',
      path: '/pages/index/index'
    }
  }
})