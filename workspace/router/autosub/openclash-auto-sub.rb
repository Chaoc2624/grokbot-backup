# merge helper for openclash-auto-sub. args: <yaml> <map> <present>; exit 0 changed, 2 unchanged
require 'yaml'
f, mapf, presf = ARGV
s = File.read(f); orig = s.dup
map = File.readlines(mapf).map { |l| l.chomp.split('=', 3) }.select { |a| a.size == 3 }
present = File.readlines(presf).map { |l| l.chomp.split('=', 2) }.select { |a| a.size == 2 }
pkeys = present.map(&:last)
TARGETS = %w[默认出口 手动 AI Telegram YouTube Google Netflix Spotify Twitter]
INFO = '剩余|套餐|到期|官网|流量|重置|过期|更新|网址|节点异常'
MULT = '倍率|倍|[2-9]x|[2-9]X|x[2-9]|×'
def gname(n, k) n =~ /[:#\[\]{},&*!|>'"%@`]|^\s|\s$/ ? k : n end
def block(s, g)
  i = s.index(/^- name: #{Regexp.escape(g)}\n/) or return nil
  j = s.index(/^(- name: |[a-z-]+:)/, i + 1) || s.size
  [i, j]
end
def prov_block(s, k)
  i = s.index(/^  #{Regexp.escape(k)}:\n/) or return nil
  j = s.index(/^(  \S|\S)/, i + 1) || s.size
  [i, j]
end
log = []
# ---- additions
pinned = map.select { |a| a[2] == 'pinned' }.map { |a| a[1] }
present.each do |n, k|
  next if pinned.include?(k)
  g = gname(n, k)
  unless prov_block(s, k)
    prov = "  #{k}:\n    type: file\n    path: \"./proxy_provider/#{k}.yaml\"\n    exclude-filter: '#{INFO}'\n" \
           "    health-check:\n      enable: true\n      url: https://www.gstatic.com/generate_204\n      interval: 600\n      timeout: 5000\n"
    s.sub!(/^proxy-groups:\n/) { prov + "proxy-groups:\n" } or abort('no proxy-groups')
    log << "+provider #{k}"
  end
  unless block(s, g)
    grp = "- name: #{g}\n  type: select\n  proxies:\n  - #{g}自动\n  use:\n  - #{k}\n" \
          "- name: #{g}自动\n  type: url-test\n  use:\n  - #{k}\n  exclude-filter: '#{MULT}'\n" \
          "  url: https://www.gstatic.com/generate_204\n  interval: 600\n  tolerance: 100\n"
    if s =~ /^- name: AI\n/ then s.sub!(/^- name: AI\n/) { grp + "- name: AI\n" } else s.sub!(/^(rule-providers|rules):\n/) { grp + $& } end
    log << "+groups #{g}"
  end
  TARGETS.each do |t|
    b = block(s, t) or next
    blk = s[b[0]...b[1]]
    next if blk.include?("  - #{g}\n")
    nb = blk =~ /^  proxies:\n/ ? blk.sub(/^  proxies:\n((?:  - [^\n]*\n)*)/) { "  proxies:\n#{$1}  - #{g}\n" } : blk.sub(/^(  type: [^\n]*\n)/) { "#{$1}  proxies:\n  - #{g}\n" }
    s[b[0]...b[1]] = nb
  end
  if (b = block(s, '英国'))
    blk = s[b[0]...b[1]]
    s[b[0]...b[1]] = blk.sub(/^  use:\n((?:  - [^\n]*\n)*)/) { "  use:\n#{$1}  - #{k}\n" } unless blk.include?("  - #{k}\n")
  end
end
# ---- removals (managed only, never pinned)
map.each do |n, k, kind|
  next if kind == 'pinned' || pkeys.include?(k)
  g = gname(n, k)
  if (b = prov_block(s, k)) then s[b[0]...b[1]] = ''; log << "-provider #{k}" end
  [g, "#{g}自动"].each { |x| if (b = block(s, x)) then s[b[0]...b[1]] = ''; log << "-group #{x}" end }
  # remove references in proxy-groups section only
  gi = s.index(/^proxy-groups:\n/); ge = s.index(/^(rule-providers|rules|sub-rules):\n/, gi) || s.size
  sec = s[gi...ge].gsub(/^  - #{Regexp.escape(g)}\n/, '').gsub(/^  - #{Regexp.escape(g)}自动\n/, '').gsub(/^  - #{Regexp.escape(k)}\n/, '')
  s[gi...ge] = sec
end
# cleanup: groups left with an empty use-list and no proxies (e.g. filter groups on a removed provider)
loop do
  gi = s.index(/^proxy-groups:\n/); ge = s.index(/^(rule-providers|rules|sub-rules):\n/, gi) || s.size
  names = s[gi...ge].scan(/^- name: ([^\n]+)$/).flatten
  dead = names.find do |nm|
    b = block(s, nm); blk = s[b[0]...b[1]]
    blk =~ /^  use:\n(?!  - )/ && blk !~ /^  proxies:\n  - /
  end
  break unless dead
  b = block(s, dead); s[b[0]...b[1]] = ''; log << "-empty group #{dead}"
  gi = s.index(/^proxy-groups:\n/); ge = s.index(/^(rule-providers|rules|sub-rules):\n/, gi) || s.size
  s[gi...ge] = s[gi...ge].gsub(/^  - #{Regexp.escape(dead)}\n/, '')
end
# safety: lock group untouched
abort('英国金融 lock changed') if (orig[/^- name: 英国金融\n(?:  [^\n]*\n)*/] != s[/^- name: 英国金融\n(?:  [^\n]*\n)*/])
if s == orig then exit 2 end
File.write(f, s); puts log.join(' ')
