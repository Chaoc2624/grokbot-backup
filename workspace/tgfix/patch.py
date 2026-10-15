import re
p="summary-engine.ts"; s=open(p,encoding="utf-8").read()
a='只返回合法 JSON：{"content":"..."}。content 使用 Markdown，必须直接从'
assert a in s; s=s.replace(a,"只总结群友实际说过的话，不加任何自己的判断、提醒、建议或标签（例如 ⚠️ 别碰、风险、伪造），数字、金额、日期和发言人必须与小时摘要完全一致。直接输出 Markdown 正文（不要 JSON、不要代码块），必须直接从")
s=s.replace("content 控制在 3500 字以内","正文控制在 3500 字以内")
i=s.index("没有真实来源时不要生成核验条目，也不要输出 JSON 之外的")
j=s.index("\\n\\n'",i)
s=s[:i]+"没有真实来源时不要生成核验条目，也不要输出正文之外的内容。"+s[j:]
old="内容。\\n\\n'\n      + windows.join('\\n\\n'))"
assert old in s; s=s.replace(old,"内容。\\n\\n')")
m=re.search(r"    const doc = await deepseekJson\(prompt, '你是严谨的中文全天摘要器，只返回合法 JSON。', 10000, 120_000\)\n    const content = [^\n]*\n    if \(!content\) throw new Error\('全天摘要内容为空'\)\n",s)
assert m; s=s.replace(m.group(0),"    const content = await dailyReduce(prompt, windows, requireFinal)\n")
anchor="async function deepseekJson("
s=s.replace(anchor, open("/tmp/helpers.ts",encoding="utf-8").read()+anchor,1)
s=s.replace("temperature: 0.1, max_tokens: maxTokens, response_format","temperature: 0.1, max_tokens: Math.min(maxTokens, DEEPSEEK_MAX_OUTPUT), response_format")
old="""    if (start < 0 || end <= start) throw new Error('DeepSeek 返回的总结不是 JSON')
    return JSON.parse(answer.slice(start, end + 1))"""
assert old in s
s=s.replace(old,"""    if (start >= 0 && end > start) { try { return JSON.parse(answer.slice(start, end + 1)) } catch { /* fall through to salvage */ } }
    const salvaged = salvageJsonContent(answer)
    if (salvaged) { console.warn('[summary-engine] salvaged truncated DeepSeek JSON'); return { content: salvaged } }
    throw new Error('DeepSeek 返回的总结不是 JSON')""")
open(p,"w",encoding="utf-8").write(s)
print("ok")
