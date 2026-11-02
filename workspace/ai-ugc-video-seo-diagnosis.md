# 哥飞 SEO Agent 诊断 — https://ai-ugc-video.com/
Chat: https://seo.web.cafe/chat/c/17fbdc02242e44b899f5d70adfaa20ed
方法: 服务器抓取（fetch_page，未执行 JS，与搜索引擎首轮抓取口径一致）2026-11-02
实测: en/zh/ja/es 首页 + robots + sitemap + /pricing + /blog + /ai/video-generator + /privacy-policy
身份: 已登录 VIP（Halo Z），无登录墙

调查过程 · 查了 14 步
已完成：抓取源码 https://ai-ugc-video.com/ 、/robots.txt 、/sitemap.xml 、/zh 、/ja 、/es 、/ai/video-generator 、/blog 、/pricing 、/privacy-policy
已完成：站内页面清单 ai-ugc-video.com
已完成：关键词难度 ai ugc video generator（KD 46 中等）、ugc video ads（KD 45 中等）
已完成：沉淀表格 ai-ugc-video.com 诊断改动清单（P0/P1/P2）15 行

## 结论
技术层干净，可以抓取、也可以收录：服务端渲染真的把内容输出到 HTML，canonical 和 hreflang 自引用都正确，robots 与 sitemap 都能返回 200；但内容层现在只有 en 和 zh 两个语言版本算是自己的：另外 8 个语言首页的 TDK 和 H1 还是模板英文，博客 4 篇全是 ShipAny 演示稿，还有占位符 What is YourAppName。这会在新站最需要信任的阶段直接拉低整站质量分。五合一也核实到了：GA4（G-453B9J3Z38）、Microsoft Clarity（z7c58ffomu）、Cloudflare Web Analytics、GSC 验证、Bing 验证五个都在。

## 一、技术层：可以抓取、可以收录
- 首页返回 200、没有跳转，未执行 JS 也照样抓到了完整的 H1、10 个 H2、正文和 FAQ 问题（HTML 有 83,933 字节，TanStack Start 的 SSR 已开启，配置里 ssr:true）→ 不存在 CSR 空壳问题。
- /privacy-policy 的 head 已完整读完，内容为：title → description → icon → 10 个 hreflang（含 x-default）→ 自引用 canonical，规范网址自洽，没有重复版本。
- robots.txt 返回 200：Allow: /，屏蔽 /admin、/settings、/api/、/*?*，并声明 sitemap。
- html lang 与语言目录一致：/=en、/zh=zh、/ja=ja、/es=es。
- 三个小瑕疵（不影响收录）：每页 head 预加载了 50+ 个 modulepreload，里面还打进了 admin_*、settings_*、common_sign_* 的后台文案包；Disallow: /*?* 把所有带参数的 URL 都屏蔽了；meta keywords 虽已废弃但仍留在页面上。

## 二、内容与 TDH 短板
| 页面 | 实测结果 | 问题 |
| --- | --- | --- |
| / | title 与 H1 一字不差，都是 “AI UGC Video Generator for Ads”；description 与首屏第一段完全相同 | 既没有品牌，也没有卖点；title 里没有免费试用、无演员、TikTok/Meta 规格这些点击理由 |
| /pricing | title “Pricing”，description “Choose the plan that works for you.” | 全站最值钱的商业页用的是模板占位 TDK，没写 6 credits、免费额度、按量付费 |
| /blog | 4 篇全是 ShipAny/TanStack 演示文，其中 What is YourAppName 是字面占位符，作者 ShipAny Team / shiponce Team / Admin | 首页 “From the blog” 还在推这几篇，整站主题被稀释 |
| /ai/video-generator | title “AI UGC Video Generator”、H1 “AI Studio”、正文只有 258 字符 | 内容很薄，还和首页抢同一个词，站内没有任何入口 |
| FAQ | 12 条问题都能抓到，但答案一条都抓不到 | 答案大概率是折叠后才渲染（根据抓取证据推断），FAQ 对爬虫几乎没有内容，也没法上 FAQPage |

全站缺 og: / twitter: 标签，也没有任何 JSON-LD（本可以上 FAQPage、SoftwareApplication、Offer）。

## 三、多语言：当前最大的重复内容集群
实测 /ja 和 /es：html lang 是 ja/es，但 title 和 H1 都是模板英文 “The headless engine for your next SaaS.”，description 是 “Auth, payments, subscriptions, credits, RBAC, CMS, and i18n — all pre-wired.”，正文除 “料金プラン”、“Precios” 两个词外全是英文。/zh 是真翻译（title「AI UGC 广告视频生成器」）。也就是说 9 个语言版本 = 同一份英文内容 + 同一份与主题无关的模板 TDK。

hreflang 只能声明“这是同一页的其他语言”，不能把 9 个语言都相同的英文内容洗白；反而会让 Google 在 10 个候选里挑一个，还把带模板 title 的页面当成低质页。另外 /zh 标 zh、zh-hant 标繁体，zh 覆盖了 zh-Hant，简体那版应标 zh-Hans。

## 四、内链与 sitemap
- sitemap 只给了 20 个 loc，全是英文（/blog 5、/docs 5、/ai 3、首页 1、/pricing 1、/updates 1、/showcases 1、/feedback 1、两条法务页），语言版本只作为 xhtml:link alternate、没有独立 loc。实际页面约 200 个，Google 只被告知了 20 个，中文首页连提交都没提交。
- 导航（Features / AI Studio / Showcases / Pricing / Blog / Docs / Feedback）里没有 /ai/image-generator、/ai/video-generator、/ai/music-generator 的入口，这三页属于孤岛页。
- 页头 “Get Started” 指向 /settings，而 robots 明确屏蔽 /settings——每个页面的主 CTA 都打向一个不让抓的地址。
- 完整页脚这一轮没读到（HTML 后半段被截断），页脚链接清单需要下次单独核。

## 五、词盘（只拿到难度，没拿到官方量）
- ai ugc video generator：哥飞版 KD 46（中等），估算月搜 3,040（KD 报告口径，规划师这次没取到，仅作量级参考）；前十里 8/10 是专门为这个词做的页面，是正面争夺的红海；最弱占位是第 1 名 ugcvideo.ai（DR 25、月流量 6.3 万、体验分 29），门槛真实存在但不厚。
- ugc video ads：KD 45.4（中等），进前十约需 50–110 个引荐域；第 2 名 createugc.ai 只注册 17 个月、DR 25 就做到月流量 15.1 万 → 这条赛道对新站友好，门票是产品体验而不是外链体量。
- 打法：首页正面打 ai ugc video generator + ugc video ads，长尾（ai ugc ads、ugc ads generator、平台规格类）交给内页，不要所有词挤在一个页面。

## 六、可执行改动清单

### P0（上线后第一周必做）
1. /blog 4 篇模板文删掉或 noindex,follow 并移出 sitemap，What is YourAppName 必须消失；首页 “From the blog” 区块先下线。
2. 8 个未真翻译的语言首页先全部 noindex 并从 hreflang/sitemap 移除，只留 en + zh 可索引；翻译完一个放一个。
3. 页头 CTA 从 /settings 改到 /pricing 或注册页。
4. /ai/video-generator 要么 noindex 移出 sitemap，要么 title 改成 AI Studio 类并补正文——现在它是和首页抢词的薄页。

### P1（1–2 周）
1. 首页 TDK 重写：title ≤60 字符加卖点+品牌（如 “AI UGC Video Generator for Ads – No Actors, No Shoot”），H1 保留核心词不再与 title 同句，description 重写（写免费试用、TikTok/Meta 规格、生成时长）。
2. FAQ 答案改成服务端渲染进首屏 HTML，配 FAQPage JSON-LD；全站补 og:title/og:image/twitter:card；价格页上 Offer/Product 结构化数据。
3. /pricing TDK 换成商业口径（6 credits、免费额度、pay as you go）。
4. sitemap 每个语言版本作独立 loc（至少先补已翻译的 /zh 全页面），加 lastmod。
5. 三个 /ai/ 工具页决定留还是删：留就进导航+页脚。
6. 用 UGC 主题文章替换模板博客，一篇文章对准一个词（ai ugc ads、ugc video specs for Meta、ai ugc vs real creator）。

### P2（顺手）
路由级代码分割，访客页面不要 preload admin_*/settings_*；Disallow: /*?* 收窄成只屏蔽已知筛选参数；删 meta keywords；空置的 /updates 移出 sitemap。

## 覆盖缺口（Agent 自己声明）
本轮工具调用额度已用尽，/de、/fr、/it、/pl、/nl-NL、/zh-hant 首页和 /docs 5 页没有逐一抓取。页脚链接清单未单独核完。下一步建议先做 P0 的多语言与模板博客，改完后在 GSC「网址移除」里对已收录的模板页请求移除，再从 sitemap 重提交。
