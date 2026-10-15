const DAILY_CHUNK_CHARS = Math.max(10_000, Number(process.env.TG_DAILY_CHUNK_CHARS || 40_000))
const DEEPSEEK_MAX_OUTPUT = 8000

function chunkWindows(windows: string[], limit: number) {
  const chunks: string[][] = []; let current: string[] = []; let size = 0
  for (const window of windows) {
    if (current.length && size + window.length > limit) { chunks.push(current); current = []; size = 0 }
    current.push(window.slice(0, limit)); size += Math.min(window.length, limit)
  }
  if (current.length) chunks.push(current)
  return chunks
}

function stripFence(text: string) {
  return text.trim().replace(/^```(?:markdown|md)?\s*/i, '').replace(/\s*```$/i, '').trim()
}

function cutToCompleteLines(text: string) {
  const index = text.lastIndexOf('\n')
  return (index > 0 ? text.slice(0, index) : text).trim()
}

async function dailyReduce(prefix: string, windows: string[], requireFinal: boolean) {
  const system = '你是严谨的中文全天摘要器，只根据给定小时摘要整理，不添加任何判断、提醒、建议或标签，数字、金额和发言人保持原样。直接输出 Markdown 正文。'
  let material = windows
  if (windows.join('\n\n').length > DAILY_CHUNK_CHARS) {
    const chunks = chunkWindows(windows, DAILY_CHUNK_CHARS)
    material = []
    for (const [index, chunk] of chunks.entries()) {
      const mapPrompt = '以下是同一天若干个小时的 Telegram 群聊小时摘要（最新小时在前）。请把它们压缩成一份该时段的中间摘要，供之后合并成全天摘要使用。'
        + '只保留群友实际说过的内容，删除机器人、入群验证和系统通知；不加任何自己的判断、提醒、建议或标签；关键数字、金额、日期、机构、链接、发言人和原话必须与原文完全一致；同一事件跨小时合并。'
        + '按“## 大类 / ### 话题”组织，直接输出 Markdown 正文，控制在 2500 字以内。\n\n' + chunk.join('\n\n')
      const part = await deepseekText(mapPrompt, system, 4000, 120_000)
      const text = part.finish === 'length' ? cutToCompleteLines(part.text) : part.text
      const first = chunk[chunk.length - 1].split('\n')[0].replace(/^###\s*/, '')
      const last = chunk[0].split('\n')[0].replace(/^###\s*/, '')
      if (text) material.push(`### 时段 ${index + 1}/${chunks.length}（${first} 至 ${last}）\n${text}`)
    }
    console.info('[summary-engine] daily map stage', `chunks=${chunks.length}`, requireFinal ? 'final' : 'incremental')
  }
  const prompt = prefix + material.join('\n\n')
  let result = await deepseekText(prompt, system, DEEPSEEK_MAX_OUTPUT, 180_000)
  if (result.finish === 'length') {
    console.warn('[summary-engine] daily summary hit the output limit; retrying with a tighter length')
    const retry = await deepseekText(prompt + '\n\n（上一次输出超长被截断。这次正文必须控制在 2500 字以内，更多合并压缩。）', system, DEEPSEEK_MAX_OUTPUT, 180_000)
    result = retry.finish === 'length' ? { text: cutToCompleteLines(retry.text), finish: 'length' } : retry
  }
  let content = result.text
  if (content.startsWith('{')) {
    try { const doc = JSON.parse(content); content = String(doc.content || doc.summary || '').trim() } catch { content = salvageJsonContent(content) || content }
  }
  if (!content) throw new Error('全天摘要内容为空')
  return content
}

async function deepseekText(prompt: string, system: string, maxTokens: number, timeoutMs: number): Promise<{ text: string; finish: string }> {
  const key = process.env.DEEPSEEK_API_KEY?.trim()
  if (!key) throw new Error('未配置 DEEPSEEK_API_KEY')
  const response = await fetch('https://api.deepseek.com/chat/completions', {
    method: 'POST',
    headers: { authorization: `Bearer ${key}`, 'content-type': 'application/json' },
    body: JSON.stringify({ model: process.env.DEEPSEEK_MODEL?.trim() || 'deepseek-chat', messages: [{ role: 'system', content: system }, { role: 'user', content: prompt }], temperature: 0.1, max_tokens: Math.min(maxTokens, DEEPSEEK_MAX_OUTPUT) }),
    signal: AbortSignal.timeout(timeoutMs),
  })
  if (!response.ok) throw new Error(`DeepSeek HTTP ${response.status}`)
  const payload = await response.json() as any
  const text = payload?.choices?.[0]?.message?.content
  if (typeof text !== 'string' || !text.trim()) throw new Error('DeepSeek 返回为空')
  return { text: stripFence(text), finish: String(payload?.choices?.[0]?.finish_reason || '') }
}

function salvageJsonContent(answer: string) {
  const match = answer.match(/"(?:content|summary|overview)"\s*:\s*"/)
  if (!match || match.index === undefined) return ''
  let raw = ''; let escaped = false
  for (const char of answer.slice(match.index + match[0].length)) {
    if (escaped) { raw += char; escaped = false; continue }
    if (char === '\\') { raw += char; escaped = true; continue }
    if (char === '"') break
    raw += char
  }
  raw = raw.replace(/\\u[0-9a-fA-F]{0,3}$/, '').replace(/\\$/, '')
  try { return cutToCompleteLines(JSON.parse(`"${raw}"`)) } catch { return '' }
}

