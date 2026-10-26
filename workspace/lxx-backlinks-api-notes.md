# `lxx.ai/backlinks` 接口与数据结构逆向笔记

## 1. 未登录状态访问结论
- **页面路由 `GET https://www.lxx.ai/backlinks`**：Next.js Middleware 直接返回 `HTTP/2 307 Temporary Redirect` 重定向至 `/login`。
- **后端 API `GET https://www.lxx.ai/api/backlinks`**：未携带登录 Cookie 时返回：
  ```json
  {"success":false,"error":"未授权","message":"用户未登录"}
  ```
- **Supabase PostgREST 直连 `GET https://qzykaszgjoudtnsztiak.supabase.co/rest/v1/backlinks?select=*`**：使用前端打包的 `anon` 密钥请求返回 `HTTP 200 []`（受 RLS 策略限制，匿名角色无法读取数据）。

---

## 2. 前端 JS Chunks 逆向出的核心配置
- **Supabase Project URL**：`https://qzykaszgjoudtnsztiak.supabase.co`
- **Supabase Anon Key**（来自 `/_next/static/chunks/4169-f19dedd3c5962c16.js`）：
  `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF6eWthc3pnam91ZHRuc3p0aWFrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0Njc2MDUsImV4cCI6MjA2MzA0MzYwNX0.3boSVeg1ofOlujHIMV_xycZIMc5uw6cFjM-zTFRwGPQ`
- **登录方式**（来自 `/_next/static/chunks/app/login/page-76f20445c8835427.js`）：
  - 支持邮箱密码登录（`supabase.auth.signInWithPassword`）
  - 支持 Google OAuth（`supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: window.location.origin + "/auth/callback" } })`）
  - 支持 GitHub OAuth
- **用户表与会员校验逻辑**（来自 `/_next/static/chunks/4504-5f270fbc6cc0c02b.js` 与 `app/page-b9521d5e57d08742.js`）：
  - 登录后前端调用 `POST /api/auth/user` 同步用户记录，并缓存至 `localStorage`（键名：`lxx_cached_user`、`lxx_cached_user_details`）。
  - 数据库 `users` 表包含字段：`id, email, name, is_paid, expiry_date, is_admin`。
  - 首页定价显示 Yearly Plan 为 `$299/year`（Stripe Checkout `/api/create-checkout-session`），免费登录用户可能只能看到部分免费外链或受 `is_paid` 字段过滤。

---

## 3. 浏览器登录 `zhangx2624@gmail.com` 后的全量提取方法

当浏览器完成 Google OAuth 登录（跳转到 `/member` 或 `/backlinks`）后，可直接在浏览器 Console 或通过携带 Cookie 调用以下任一方式拉取全量外链数据：

### 方式 A：直接请求 Next.js 后端接口 `/api/backlinks`
在已登录的浏览器页面执行：
```javascript
const res = await fetch('/api/backlinks', { credentials: 'include' });
const data = await res.json();
console.log(data);
```
（若支持分页参数如 `?page=1&limit=1000` 或返回全量数组，可直接写入 `/workspace/lxx-backlinks-raw.json`。）

### 方式 B：使用已登录用户的 Supabase `access_token` 直连 PostgREST `backlinks` 表
从浏览器 `document.cookie`（`sb-qzykaszgjoudtnsztiak-auth-token`）或 `localStorage` 获取用户的 `access_token` 后，在 `/workspace` 执行：
```bash
curl -s "https://qzykaszgjoudtnsztiak.supabase.co/rest/v1/backlinks?select=*&order=dr.desc.nullslast" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF6eWthc3pnam91ZHRuc3p0aWFrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0Njc2MDUsImV4cCI6MjA2MzA0MzYwNX0.3boSVeg1ofOlujHIMV_xycZIMc5uw6cFjM-zTFRwGPQ" \
  -H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
  -o /workspace/lxx-backlinks-raw.json
```
