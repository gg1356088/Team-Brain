# 浏览器自动化测试陷阱

记录时间：2026-06-09

## 经验教训

### Google 表单自动填写 → 被拦截

**场景：** 尝试用 `browser_type` 自动填写 Google 表单并点击"Next"。

**结果：** Google 显示"此浏览器或应用可能不安全"，阻止操作。

**原因：** Google 对自动化工具有严格的 bot 检测（reCAPTCHA、行为模式分析、设备指纹）。Hermes 的浏览器工具走的是 CDP（Chrome DevTools Protocol），没有人类交互的随机延迟和行为模拟，直接触发拦截。

**结论：** 不要用浏览器工具测试 Google 表单或任何 Google 账号相关页面。大厂对自动化的封锁非常严格。

### 替代测试方案

如果需要对表单/页面做自动化测试：
1. **用自己的测试表单** — 创建一个非 Google 的简单表单页面
2. **使用 Mock 服务** — 比如 Formspree、Google Forms 的测试版
3. **本地搭建测试页面** — 用一个简单的 HTML 表单做测试

### snapshot vs vision 配合策略

**`browser_snapshot`** — 返回页面元素的可访问性树（ref IDs、文本）。快但可能漏掉动态内容。

**`browser_vision`** — 截取页面截图做视觉分析。能看到所有渲染内容，包括动态加载的。慢但全面。

**最佳实践：**
- 简单页面/静态内容 → 用 `browser_snapshot` 就行
- 动态页面/表单不确定时 → 先用 `snapshot` 拿 ref，再用 `vision` 截图确认
- 表单填写失败时 → 用 `vision` 检查页面是否加载完整，元素是否到位

### 大厂页面自动化通用规则

| 网站 | 能否自动化 | 说明 |
|------|-----------|------|
| Google Docs/Forms | 不能 | 强 bot 检测 |
| Gmail | 不能 | 需要 OAuth，有 bot 检测 |
| 普通 HTML 表单 | 可以 | 用 snapshot + type |
| 本地测试页面 | 可以 | 完全可控 |
| 电商/论坛 | 看情况 | 动态内容多，需要 vision |
