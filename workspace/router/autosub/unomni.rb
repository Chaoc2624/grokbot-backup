f=ARGV[0]; s=File.read(f)
def block(s, g)
  i = s.index(/^- name: #{Regexp.escape(g)}\n/) or return nil
  j = s.index(/^(- name: |[a-z-]+:)/, i + 1) || s.size
  [i, j]
end
%w[omni-sub omni-sub自动].each { |x| if (b = block(s, x)) then s[b[0]...b[1]] = '' end }
gi = s.index(/^proxy-groups:\n/); ge = s.index(/^(rule-providers|rules|sub-rules):\n/, gi)
s[gi...ge] = s[gi...ge].gsub(/^  - omni-sub\n/, '').gsub(/^  - omni-sub自动\n/, '')
File.write(f, s); puts "cleaned #{f}"
