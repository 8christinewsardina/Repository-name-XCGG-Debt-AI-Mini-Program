微信小程序对接说明（示例）

概述
- 后端提供异步分析接口：
  - POST /api/v1/reports/start  提交 FinancialStatement，返回 { job_id }
  - GET  /api/v1/reports/{job_id} 查询任务状态和结果

安全与 CORS
- 后端已启用 CORS（开发允许所有来源）。生产需将 `allow_origins` 限制为小程序代理域。
- 后端 Gemini 调用受 `GEMINI_ENABLED`/`GEMINI_API_KEY` 门控。

示例：提交分析并轮询（微信小程序）

在小程序页面的 JS 中：

```javascript
// pages/index/index.js
Page({
  data: {
    jobId: null,
    status: null,
    result: null,
  },

  startReport() {
    const payload = {
      assets: 100000,
      liabilities: 20000,
      income: 10000,
      expenses: 5000
    };

    wx.request({
      url: 'https://api.example.com/api/v1/reports/start',
      method: 'POST',
      data: payload,
      header: { 'content-type': 'application/json' },
      success: (res) => {
        const jobId = res.data.job_id;
        this.setData({ jobId, status: 'queued' });
        this.pollJob(jobId);
      },
      fail: (err) => {
        wx.showToast({ title: '提交失败', icon: 'none' });
      }
    });
  },

  pollJob(jobId) {
    const poll = () => {
      wx.request({
        url: `https://api.example.com/api/v1/reports/${jobId}`,
        method: 'GET',
        success: (res) => {
          const job = res.data;
          this.setData({ status: job.status });
          if (job.status === 'done') {
            this.setData({ result: job.result });
            wx.showToast({ title: '分析完成', icon: 'success' });
          } else if (job.status === 'error') {
            wx.showToast({ title: '分析出错', icon: 'none' });
          } else {
            // 继续轮询
            setTimeout(poll, 1500);
          }
        },
        fail: () => {
          setTimeout(poll, 3000);
        }
      });
    };
    poll();
  }
});
```

备注
- 请替换 `https://api.example.com` 为你的 API 地址或代理地址（若小程序需要域名白名单）。
- 真实环境中需处理鉴权/速率限制与错误提示。
