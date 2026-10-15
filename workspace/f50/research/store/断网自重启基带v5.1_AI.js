//<script>
(() => {
  const CONTAINER_SELECTOR = '.functions-container';
  const PANEL_ID = 'baseband_panel';

  const BUILTIN_SCRIPT_BASE64 = 'IyEvc3lzdGVtL2Jpbi9zaAojIOWfuuW4pue9kee7nOajgOa1i+acjeWKoSB2Ni4wICjmlK/mjIEgc3RhcnQvc3RvcC9yZXN0YXJ0L3N0YXR1cykKClZFUlNJT049IjYuMCIKQkFTRV9ESVI9Ii9kYXRhL2thbm9fcmVzdGFydF9iYXNlYmFuZCIKTE9HX0RJUj0iL3NkY2FyZC9rYW5vX2Jhc2ViYW5kIgpMT0dfRklMRT0iJHtMT0dfRElSfS9iYXNlYmFuZF9yZXN0YXJ0LmxvZyIKUElEX0ZJTEU9IiR7QkFTRV9ESVJ9L3NlcnZpY2UucGlkIgpUSU1FX01PTklUT1JfUElEX0ZJTEU9IiR7QkFTRV9ESVJ9L3RpbWVfbW9uaXRvci5waWQiClBBVVNFX0ZJTEU9IiR7QkFTRV9ESVJ9L3BhdXNlX2ZsYWciCgpCQVNFX1VSTD0iaHR0cDovLzE5Mi4xNjguMC4xOjIzMzMiCkNIRUNLX0lOVEVSVkFMPTMwClJFVFJZX0lOVEVSVkFMPTM2MDAgICAgICAgICAgIyDmlq3nvZHop6blj5HplIHlrpox5bCP5pe2CkZBSUxfVEhSRVNIT0xEPTUKUkVUUllfU0xFRVA9MgpUSU1FX0NIRUNLX0lOVEVSVkFMPTM2MDAKCklQMT0iMTE5LjI5LjI5LjI5IgpJUDI9IjIyMy41LjUuNSIKSVAzPSIyMjMuNi42LjYiCk5BTUUxPSLohb7orq9ETlMiCk5BTUUyPSLpmL/ph4xETlMiCk5BTUUzPSLpmL/ph4xETlMyIgoKbWtkaXIgLXAgIiRCQVNFX0RJUiIgIiRMT0dfRElSIiAyPi9kZXYvbnVsbAp0b3VjaCAiJExPR19GSUxFIiAyPi9kZXYvbnVsbAoKbG9nKCkgewogICAgZWNobyAiJChkYXRlICcrJVktJW0tJWQgJUg6JU06JVMnKSAkMSIgPj4gIiRMT0dfRklMRSIKfQoKc2VuZF9hdCgpIHsKICAgIGxvY2FsIGNtZD0iJDEiCiAgICBsb2NhbCBlbmNvZGVkPSQoZWNobyAtbiAiJGNtZCIgfCBzZWQgJ3MvKy8lMkIvZzsgcy89LyUzRC9nOyBzLywvJTJDL2cnKQogICAgY3VybCAtcyAiJHtCQVNFX1VSTH0vYXBpL0FUP2NvbW1hbmQ9JHtlbmNvZGVkfSZzbG90PTAiIDI+L2Rldi9udWxsCn0KCnJlc3RhcnRfYmFzZWJhbmQoKSB7CiAgICBsb2cgIlvph43lkK9dIOaJp+ihjCBBVCtDRlVOPTEsMSIKICAgIGxvY2FsIHJlc3VsdD0kKHNlbmRfYXQgIkFUK0NGVU49MSwxIikKICAgIGxvZyAiW+mHjeWQr10g5o6l5Y+j5ZON5bqUOiAkcmVzdWx0IgogICAgZWNobyAiJHJlc3VsdCIgfCBncmVwIC1xICdPSycgJiYgbG9nICJb6YeN5ZCvXSDln7rluKbph43lkK/mjIfku6Tlt7Llj5HpgIEiIHx8IGxvZyAiW+mHjeWQr10g5Z+65bim6YeN5ZCv5oyH5Luk5Y+v6IO95aSx6LSlIgp9Cgpsb2NrX3Jlc3RhcnQoKSB7CiAgICBsb2NhbCBsb2NrX3NlYz0kMQogICAgZWNobyAicGF1c2UiID4gIiRQQVVTRV9GSUxFIgogICAgbG9nICJb6ZSB5a6aXSDov5vlhaUgJHtsb2NrX3NlY30g56eS6ZSB5a6a5pyfIgogICAgbG9jYWwgZWxhcHNlZD0wCiAgICB3aGlsZSBbICRlbGFwc2VkIC1sdCAkbG9ja19zZWMgXSAmJiBbIC1mICIkUEFVU0VfRklMRSIgXTsgZG8KICAgICAgICBzbGVlcCAxMAogICAgICAgIGVsYXBzZWQ9JCgoZWxhcHNlZCArIDEwKSkKICAgIGRvbmUKICAgIHJtIC1mICIkUEFVU0VfRklMRSIgMj4vZGV2L251bGwKICAgIGxvZyAiW+mUgeWuml0g6ZSB5a6a5pyf57uT5p2fIgp9CgpjaGVja19uZXR3b3JrKCkgewogICAgbG9jYWwgcmV0cnk9MAogICAgd2hpbGUgWyAkcmV0cnkgLWx0IDMgXTsgZG8KICAgICAgICBsb2NhbCBpcDFfb2s9MCBpcDJfb2s9MCBpcDNfb2s9MAogICAgICAgIHBpbmcgLWMgMSAtVyAzICRJUDEgPi9kZXYvbnVsbCAyPiYxICYmIGlwMV9vaz0xCiAgICAgICAgcGluZyAtYyAxIC1XIDMgJElQMiA+L2Rldi9udWxsIDI+JjEgJiYgaXAyX29rPTEKICAgICAgICBwaW5nIC1jIDEgLVcgMyAkSVAzID4vZGV2L251bGwgMj4mMSAmJiBpcDNfb2s9MQoKICAgICAgICBpZiBbICRpcDFfb2sgLWVxIDEgXSB8fCBbICRpcDJfb2sgLWVxIDEgXSB8fCBbICRpcDNfb2sgLWVxIDEgXTsgdGhlbgogICAgICAgICAgICBsb2NhbCBzMT0iJChbICRpcDFfb2sgLWVxIDEgXSAmJiBlY2hvIE9LIHx8IGVjaG8gRkFJTCkiCiAgICAgICAgICAgIGxvY2FsIHMyPSIkKFsgJGlwMl9vayAtZXEgMSBdICYmIGVjaG8gT0sgfHwgZWNobyBGQUlMKSIKICAgICAgICAgICAgbG9jYWwgczM9IiQoWyAkaXAzX29rIC1lcSAxIF0gJiYgZWNobyBPSyB8fCBlY2hvIEZBSUwpIgogICAgICAgICAgICBsb2cgIlvnvZHnu5xdICR7TkFNRTF9PSRzMSwgJHtOQU1FMn09JHMyLCAke05BTUUzfT0kczMgLT4gUEFTUyIKICAgICAgICAgICAgcmV0dXJuIDAKICAgICAgICBlbHNlCiAgICAgICAgICAgIGxvZyAiW+e9kee7nF0g5YWo6YOoUGluZ+Wksei0pSAo6YeN6K+VICQoKHJldHJ5KzEpKS8zKSIKICAgICAgICAgICAgcmV0cnk9JCgocmV0cnkrMSkpCiAgICAgICAgICAgIHNsZWVwIDIKICAgICAgICBmaQogICAgZG9uZQogICAgbG9nICJb572R57ucXSDov57nu60z5qyh5qOA5rWL5YWo6YOo5aSx6LSlIC0+IEZBSUwiCiAgICByZXR1cm4gMQp9CgpnZXRfY29ubmVjdGVkX3NlY29uZHMoKSB7CiAgICBsb2NhbCBjbWRfbGlzdD0idXNiX3BvcnRfc3dpdGNoLGJhdHRlcnlfY2hhcmdpbmcsc21zX3JlY2VpdmVkX2ZsYWcsc21zX3VucmVhZF9udW0sc21zX3NpbV91bnJlYWRfbnVtLHNpbV9tc2lzZG4sZGF0YV92b2x1bWVfbGltaXRfc3dpdGNoLGJhdHRlcnlfdmFsdWUsYmF0dGVyeV92b2xfcGVyY2VudCxuZXR3b3JrX3NpZ25hbGJhcixuZXR3b3JrX3Jzc2ksY3JfdmVyc2lvbixpY2NpZCxpbWVpLGltc2ksaXB2Nl93YW5faXBhZGRyLGxhbl9pcGFkZHIsbWFjX2FkZHJlc3MsbXNpc2RuLG5ldHdvcmtfaW5mb3JtYXRpb24sTHRlX2NhX3N0YXR1cyxyc3NpLFo1Z19yc3JwLGx0ZV9yc3JwLHdpZmlfYWNjZXNzX3N0YV9udW0sbG9naW5mbyxkYXRhX3ZvbHVtZV9hbGVydF9wZXJjZW50LGRhdGFfdm9sdW1lX2xpbWl0X3NpemUscmVhbHRpbWVfcnhfdGhycHQscmVhbHRpbWVfdHhfdGhycHQscmVhbHRpbWVfdGltZSxtb250aGx5X3R4X2J5dGVzLG1vbnRobHlfcnhfYnl0ZXMsbW9udGhseV90aW1lLG5ldHdvcmtfdHlwZSxuZXR3b3JrX3Byb3ZpZGVyLHBwcF9zdGF0dXMiCiAgICBsb2NhbCB1cmw9IiR7QkFTRV9VUkx9L2FwaS9nb2Zvcm0vZ29mb3JtX2dldF9jbWRfcHJvY2Vzcz9tdWx0aV9kYXRhPTEmaXNUZXN0PWZhbHNlJmNtZD0ke2NtZF9saXN0fSIKICAgIGxvY2FsIHJlc3A9JChjdXJsIC1zICIkdXJsIiAyPi9kZXYvbnVsbCkKICAgIGVjaG8gIiRyZXNwIiB8IHNlZCAtbiAncy8uKiJyZWFsdGltZV90aW1lIjoiKlwoWzAtOV0qXCkiKi4qL1wxL3AnIHwgaGVhZCAtMQp9Cgp0aW1lX21vbml0b3JfbG9vcCgpIHsKICAgIGxvZyAiW+aXtumVv10g562J5b6FIDEyMCDnp5LlkI7lvIDlp4vpppbmrKHmo4DmtYsuLi4iCiAgICBzbGVlcCAxMjAKICAgIHdoaWxlIHRydWU7IGRvCiAgICAgICAgbG9jYWwgc2Vjb25kcz0kKGdldF9jb25uZWN0ZWRfc2Vjb25kcykKICAgICAgICBpZiBbIC1uICIkc2Vjb25kcyIgXTsgdGhlbgogICAgICAgICAgICBsb2cgIlvml7bplb9dIOajgOafpe+8muW3sui/nuaOpSAke3NlY29uZHN9IOenkiAoJCgoc2Vjb25kcy8zNjAwKSnlsI/ml7YgJCgoKHNlY29uZHMlMzYwMCkvNjApKeWIhikiCiAgICAgICAgICAgIGlmIFsgIiRzZWNvbmRzIiAtZ2UgNDMyMDAgXTsgdGhlbgogICAgICAgICAgICAgICAgaWYgWyAtZiAiJFBBVVNFX0ZJTEUiIF07IHRoZW4KICAgICAgICAgICAgICAgICAgICBsb2cgIlvml7bplb9dIOajgOa1i+WIsOmUgeWumuagh+iusO+8jOi3s+i/h+acrOasoemHjeWQryIKICAgICAgICAgICAgICAgIGVsc2UKICAgICAgICAgICAgICAgICAgICBsb2cgIlvml7bplb9dIOaJp+ihjOWfuuW4pumHjeWQr++8iOmUgeWumjLliIbpkp/vvIkiCiAgICAgICAgICAgICAgICAgICAgcmVzdGFydF9iYXNlYmFuZAogICAgICAgICAgICAgICAgICAgIGxvY2tfcmVzdGFydCAxMjAKICAgICAgICAgICAgICAgIGZpCiAgICAgICAgICAgIGZpCiAgICAgICAgZWxzZQogICAgICAgICAgICBsb2cgIlvml7bplb9dIOacquiDveiOt+WPlui/nuaOpeaXtumVvyIKICAgICAgICBmaQogICAgICAgIHNsZWVwICRUSU1FX0NIRUNLX0lOVEVSVkFMCiAgICBkb25lCn0KCnByZWNoZWNrX25ldHdvcmsoKSB7CiAgICBsb2cgIlvpooTmo4BdIOW8gOWni+etieW+hee9kee7nOWwsee7qu+8iOacgOmVvyA1IOWIhumSn++8iSIKICAgIGxvY2FsIG1heF9hdHRlbXB0cz0zMCAgIyAzMCAqIDEwcyA9IDMwMHMKICAgIGxvY2FsIGF0dGVtcHQ9MAogICAgd2hpbGUgWyAkYXR0ZW1wdCAtbHQgJG1heF9hdHRlbXB0cyBdOyBkbwogICAgICAgIGlmIGNoZWNrX25ldHdvcms7IHRoZW4KICAgICAgICAgICAgbG9nICJb6aKE5qOAXSDnvZHnu5zlt7LlsLHnu6oiCiAgICAgICAgICAgIHJldHVybiAwCiAgICAgICAgZmkKICAgICAgICBhdHRlbXB0PSQoKGF0dGVtcHQgKyAxKSkKICAgICAgICBsb2cgIlvpooTmo4BdIOesrCAkYXR0ZW1wdC8ke21heF9hdHRlbXB0c30g5qyh5qOA5rWL5aSx6LSl77yM562J5b6FIDEwIOenki4uLiIKICAgICAgICBzbGVlcCAxMAogICAgZG9uZQogICAgbG9nICJb6aKE5qOAXSDnrYnlvoXotoXml7bvvIznvZHnu5zku43mnKrlsLHnu6rvvIznu6fnu63lkK/liqjkvYblj6/og73lvbHlk43lip/og70iCiAgICByZXR1cm4gMCAgICMg5pS55Li66L+U5ZueIDDvvIzorqnmnI3liqHnu6fnu63ov5DooYzvvIzkvYblkI7nu63lvqrnjq/ku43kvJrmo4DmtYsKfQoKcnVuX3NlcnZpY2UoKSB7CiAgICBsb2cgIlt2JFZFUlNJT05dIOacjeWKoeS4u+i/m+eoi+W3suWQr+WKqCAoUElEICQkKSIKICAgIGxvZyAiW+mFjee9rl0g5qOA5rWL6Ze06ZqUICR7Q0hFQ0tfSU5URVJWQUx9c++8jOaWree9kemUgeWumiAke1JFVFJZX0lOVEVSVkFMfXMiCiAgICBsb2cgIlvphY3nva5dIOi/nue7reWksei0pemYiOWAvCAke0ZBSUxfVEhSRVNIT0xEfe+8jOmHjeivlemXtOmalCAke1JFVFJZX1NMRUVQfXMiCiAgICBsb2cgIlvml7bplb9dIOebkeaOp+mXtOmalCAke1RJTUVfQ0hFQ0tfSU5URVJWQUx9c++8jOmmluasoeajgOa1i+W7tui/nyAxMjBzIgoKICAgICMg6aKE5qOA77yI562J5b6F572R57uc5bCx57uq77yJCiAgICBwcmVjaGVja19uZXR3b3JrCgogICAgIyDlkK/liqjml7bplb/nm5HmjqflrZDov5vnqIsKICAgIHRpbWVfbW9uaXRvcl9sb29wICYKICAgIGxvY2FsIHRpbWVfcGlkPSQhCiAgICBlY2hvICIkdGltZV9waWQiID4gIiRUSU1FX01PTklUT1JfUElEX0ZJTEUiCiAgICBsb2cgIlvml7bplb9dIOaXtumVv+ebkeaOp+i/m+eoiyBQSUQ9JHRpbWVfcGlkIgoKICAgICMg5Li75b6q546vCiAgICBsb2NhbCBmYWlsX2NvdW50PTAKICAgIHdoaWxlIHRydWU7IGRvCiAgICAgICAgaWYgWyAtZiAiJFBBVVNFX0ZJTEUiIF07IHRoZW4KICAgICAgICAgICAgbG9nICJb5Li75b6q546vXSDplIHlrprkuK3vvIzot7Pov4fmo4DmtYsiCiAgICAgICAgICAgIHNsZWVwICR7Q0hFQ0tfSU5URVJWQUx9CiAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgZmkKCiAgICAgICAgaWYgY2hlY2tfbmV0d29yazsgdGhlbgogICAgICAgICAgICBmYWlsX2NvdW50PTAKICAgICAgICBlbHNlCiAgICAgICAgICAgIGZhaWxfY291bnQ9JCgoZmFpbF9jb3VudCArIDEpKQogICAgICAgICAgICBsb2cgIlvkuLvlvqrnjq9dIOe9kee7nOW8guW4uO+8jOi/nue7reWksei0pSAke2ZhaWxfY291bnR9LyR7RkFJTF9USFJFU0hPTER9IgogICAgICAgICAgICBpZiBbICRmYWlsX2NvdW50IC1nZSAkRkFJTF9USFJFU0hPTEQgXTsgdGhlbgogICAgICAgICAgICAgICAgbG9nICJb5Li75b6q546vXSDovr7liLDpmIjlgLzvvIzmiafooYzln7rluKbph43lkK/vvIjplIHlrpogJHtSRVRSWV9JTlRFUlZBTH1z77yJIgogICAgICAgICAgICAgICAgcmVzdGFydF9iYXNlYmFuZAogICAgICAgICAgICAgICAgbG9ja19yZXN0YXJ0ICRSRVRSWV9JTlRFUlZBTAogICAgICAgICAgICAgICAgZmFpbF9jb3VudD0wCiAgICAgICAgICAgIGVsc2UKICAgICAgICAgICAgICAgIHNsZWVwICRSRVRSWV9TTEVFUAogICAgICAgICAgICBmaQogICAgICAgIGZpCiAgICAgICAgc2xlZXAgJHtDSEVDS19JTlRFUlZBTH0KICAgIGRvbmUKfQoKIyAtLS0tLS0tLS0tIOWPguaVsOWkhOeQhiAtLS0tLS0tLS0tCmNhc2UgIiQxIiBpbgogICAgc3RhcnQpCiAgICAgICAgaWYgWyAtZiAiJFBJRF9GSUxFIiBdICYmIGtpbGwgLTAgJChjYXQgIiRQSURfRklMRSIpIDI+L2Rldi9udWxsOyB0aGVuCiAgICAgICAgICAgIGVjaG8gIuacjeWKoeW3suWcqOi/kOihjCAoUElEICQoY2F0ICRQSURfRklMRSkpIgogICAgICAgICAgICBleGl0IDEKICAgICAgICBmaQogICAgICAgICMg5ZCv5Yqo5ZCO5Y+w5pyN5Yqh77yM5L2/55SoIG5vaHVwIOWSjCAmIOiuqeeItui/m+eoi+mAgOWHugogICAgICAgICMg5oqK6L6T5Ye66YeN5a6a5ZCR5YiwIC9kZXYvbnVsbO+8jOaXpeW/l+iHquW3seWGmQogICAgICAgIG5vaHVwIC9zeXN0ZW0vYmluL3NoICIkMCIgcnVuID4vZGV2L251bGwgMj4mMSAmCiAgICAgICAgc2xlZXAgMQogICAgICAgIGlmIFsgLWYgIiRQSURfRklMRSIgXSAmJiBraWxsIC0wICQoY2F0ICIkUElEX0ZJTEUiKSAyPi9kZXYvbnVsbDsgdGhlbgogICAgICAgICAgICBlY2hvICJzdGFydGVkIiAgICMg5YWz6ZSu77ya5YmN56uv6Z2g5q2k5Yik5pat5oiQ5YqfCiAgICAgICAgICAgIGxvZyAiW+WQr+WKqF0g5pyN5Yqh5bey5ZCv5Yqo77yMUElEPSQoY2F0ICRQSURfRklMRSkiCiAgICAgICAgICAgIGV4aXQgMAogICAgICAgIGVsc2UKICAgICAgICAgICAgZWNobyAi5ZCv5Yqo5aSx6LSl77yM6K+35p+l55yL5pel5b+XIgogICAgICAgICAgICBleGl0IDEKICAgICAgICBmaQogICAgICAgIDs7CgogICAgc3RvcCkKICAgICAgICBpZiBbICEgLWYgIiRQSURfRklMRSIgXTsgdGhlbgogICAgICAgICAgICBlY2hvICLmnI3liqHmnKrov5DooYwiCiAgICAgICAgICAgIGV4aXQgMQogICAgICAgIGZpCiAgICAgICAgcGlkPSQoY2F0ICIkUElEX0ZJTEUiKQogICAgICAgIGtpbGwgLVRFUk0gIiRwaWQiIDI+L2Rldi9udWxsCiAgICAgICAgIyDnrYnlvoXov5vnqIvpgIDlh7oKICAgICAgICBmb3IgaSBpbiAxIDIgMyA0IDU7IGRvCiAgICAgICAgICAgIGlmICEga2lsbCAtMCAiJHBpZCIgMj4vZGV2L251bGw7IHRoZW4KICAgICAgICAgICAgICAgIGJyZWFrCiAgICAgICAgICAgIGZpCiAgICAgICAgICAgIHNsZWVwIDEKICAgICAgICBkb25lCiAgICAgICAgIyDlvLrliLbmnYDmrbsKICAgICAgICBraWxsIC05ICIkcGlkIiAyPi9kZXYvbnVsbAogICAgICAgIHJtIC1mICIkUElEX0ZJTEUiICIkVElNRV9NT05JVE9SX1BJRF9GSUxFIgogICAgICAgIGVjaG8gIuW3suWBnOatoiIKICAgICAgICBsb2cgIlvlgZzmraJdIOacjeWKoeW3suWBnOatoiIKICAgICAgICBleGl0IDAKICAgICAgICA7OwoKICAgIHJlc3RhcnQpCiAgICAgICAgIiQwIiBzdG9wCiAgICAgICAgc2xlZXAgMQogICAgICAgICIkMCIgc3RhcnQKICAgICAgICA7OwoKICAgIHN0YXR1cykKICAgICAgICBpZiBbIC1mICIkUElEX0ZJTEUiIF0gJiYga2lsbCAtMCAkKGNhdCAiJFBJRF9GSUxFIikgMj4vZGV2L251bGw7IHRoZW4KICAgICAgICAgICAgZWNobyAi6L+Q6KGM5LitIChQSUQgJChjYXQgJFBJRF9GSUxFKSkiCiAgICAgICAgICAgIGV4aXQgMAogICAgICAgIGVsc2UKICAgICAgICAgICAgZWNobyAi5pyq6L+Q6KGMIgogICAgICAgICAgICBleGl0IDEKICAgICAgICBmaQogICAgICAgIDs7CgogICAgcnVuKQogICAgICAgICMg5YaF6YOo5L2/55So77yM55So5LqO5ZCv5Yqo5ZCO5Y+w5Li76L+b56iLCiAgICAgICAgIyDlhpnlhaUgUElEIOaWh+S7tu+8iOW9k+WJjSBzaGVsbCDnmoQgUElE77yJCiAgICAgICAgZWNobyAkJCA+ICIkUElEX0ZJTEUiCiAgICAgICAgIyDpgb/lhY3ph43lpI3ov5DooYzvvIjkvYblpJbpg6jlt7LmnInmo4Dmn6XvvIzov5nph4zlho3mo4Dmn6XkuIDmrKHvvIkKICAgICAgICAjIOWQr+WKqOacjeWKoQogICAgICAgIHJ1bl9zZXJ2aWNlCiAgICAgICAgIyDlpoLmnpwgcnVuX3NlcnZpY2Ug5oSP5aSW6YCA5Ye677yM5Yig6ZmkIFBJRCDmlofku7YKICAgICAgICBybSAtZiAiJFBJRF9GSUxFIgogICAgICAgIDs7CgogICAgKikKICAgICAgICBlY2hvICLnlKjms5U6ICQwIHtzdGFydHxzdG9wfHJlc3RhcnR8c3RhdHVzfSIKICAgICAgICBleGl0IDEKICAgICAgICA7Owplc2Fj';

  const BASE_DIR = '/data/kano_restart_baseband';
  const SERVICE_SH = `${BASE_DIR}/service.sh`;
  const PID_FILE = `${BASE_DIR}/service.pid`;
  const LOG_DIR = '/sdcard/kano_baseband';
  const LOG_FILE = `${LOG_DIR}/baseband_restart.log`;
  const USER_SERVICE_SH = `${LOG_DIR}/service.sh`;
  const BOOT_SH = '/sdcard/ufi_tools_boot.sh';
  const BOOT_LINE = `sh ${SERVICE_SH} start`;
  const API_BASE = 'http://192.168.0.1:2333';

  const INSTALLED_FLAG = `${BASE_DIR}/.installed`;
  const BOOT_FLAG = `${BASE_DIR}/.boot_enabled`;

  const state = {
    busy: false,
    serviceRunning: false,
    bootEnabled: false,
    installed: false,
    hasUserScript: false,
    logContent: '',
    refreshedAt: '',
    autoRefresh: false,
    autoRefreshTimer: null,
    collapsed: true,
    ping: { baidu: '-', aliyun: '-', tencent: '-', google: '-', youtube: '-', bilibili: '-' },
    connectedTime: '--',
  };

  const run = async (cmd, timeout = 15000) => {
    const res = await runShellWithRoot(cmd + ' 2>&1', timeout);
    return { ok: Boolean(res?.success), content: String(res?.content || '').trim() };
  };
  const shellQuote = (v) => `'${String(v ?? '').replace(/'/g, `'\\''`)}'`;

  const highlightKeywords = (text) => {
    if (!text) return '';
    let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const regex = /\b(fail|ok|pass)\b|失败/gi;
    return escaped.replace(regex, (match) => {
      const lower = match.toLowerCase();
      let color;
      if (lower === 'fail' || match === '失败') color = '#DC143C';
      else if (lower === 'ok') color = '#20B2AA';
      else if (lower === 'pass') color = '#3CB371';
      return `<span style="color:${color};">${match}</span>`;
    });
  };

  const killAll = async () => {
    await run(`
      [ -f ${shellQuote(PID_FILE)} ] && kill -TERM $(cat ${shellQuote(PID_FILE)}) 2>/dev/null
      sleep 1
      [ -f ${shellQuote(PID_FILE)} ] && kill -9 $(cat ${shellQuote(PID_FILE)}) 2>/dev/null
      rm -f ${shellQuote(PID_FILE)}
      ps -ef 2>/dev/null | grep -E '${BASE_DIR}/service.sh|kano_restart_baseband' | grep -v grep | awk '{print $2}' | while read pid; do
        [ -n "$pid" ] && kill -9 $pid 2>/dev/null
      done
    `, 8000);
  };

  const readStatus = async () => {
    const r = await run(`
      installed_flag=0; boot_flag=0; script_exists=0; running=0; user_script=0
      [ -f ${shellQuote(INSTALLED_FLAG)} ] && installed_flag=1
      [ -f ${shellQuote(BOOT_FLAG)} ] && boot_flag=1
      [ -f ${shellQuote(SERVICE_SH)} ] && script_exists=1
      [ -f ${shellQuote(PID_FILE)} ] && kill -0 $(cat ${shellQuote(PID_FILE)}) 2>/dev/null && running=1
      [ -f ${shellQuote(USER_SERVICE_SH)} ] && user_script=1
      echo installed=$installed_flag
      echo boot=$boot_flag
      echo script_exists=$script_exists
      echo running=$running
      echo user_script=$user_script
    `);
    const text = r.content;
    const installed = /installed=1/.test(text) || /script_exists=1/.test(text);
    const bootFromFlag = /boot=1/.test(text);
    const bootCheck = await run(`grep -qxF ${shellQuote(BOOT_LINE)} ${shellQuote(BOOT_SH)} 2>/dev/null && echo 1 || echo 0`);
    const bootFromFile = bootCheck.content.trim() === '1';

    state.installed = installed;
    state.bootEnabled = bootFromFlag || bootFromFile;
    state.serviceRunning = /running=1/.test(text);
    state.hasUserScript = /user_script=1/.test(text);

    if (state.installed && !/installed=1/.test(text)) {
      await run(`touch ${shellQuote(INSTALLED_FLAG)}`);
    }
    if (state.bootEnabled && !/boot=1/.test(text)) {
      await run(`touch ${shellQuote(BOOT_FLAG)}`);
    }
    return { installed: state.installed, hasUserScript: state.hasUserScript };
  };

  const loadLog = async () => {
    const r = await run(`[ -f ${shellQuote(LOG_FILE)} ] && tail -n 100 ${shellQuote(LOG_FILE)}`, 5000);
    state.logContent = r.content || '（暂无日志）';
    state.refreshedAt = new Date().toLocaleString('zh-CN', { hour12: false });
    const el = document.querySelector('#bb_log_text');
    if (el) {
      el.innerHTML = highlightKeywords(state.logContent);
      el.scrollTop = el.scrollHeight;
    }
    const timeEl = document.querySelector('#bb_log_time');
    if (timeEl) timeEl.textContent = '刷新: ' + state.refreshedAt;
  };

  const fetchConnectedTime = async () => {
    try {
      const timestamp = Date.now();
      const url = `${API_BASE}/api/goform/goform_get_cmd_process?multi_data=1&isTest=false&cmd=realtime_time&_=${timestamp}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const seconds = parseInt(data['realtime_time']) || 0;
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      const s = seconds % 60;
      const timeStr = `${h}时${m}分${s}秒`;
      state.connectedTime = timeStr;
      const el = document.querySelector('#bb_log_time_mini');
      if (el) el.textContent = `距上次断网重启基带: ${timeStr}`;
    } catch (e) {
      state.connectedTime = '--';
      const el = document.querySelector('#bb_log_time_mini');
      if (el) el.textContent = '获取中: --';
    }
  };

  const renderPingDisplay = () => {
    const el = document.querySelector('#bb_ping_display');
    if (!el) return;
    const labelMap = {
      baidu: '百度',
      aliyun: '阿里',
      tencent: '腾讯',
      bilibili: 'Bili',
      google: '谷歌',
      youtube: '油管'
    };
    const parts = [];
    for (const [key, label] of Object.entries(labelMap)) {
      const val = state.ping[key] ?? '-';
      const valueColor = (val === '超时') ? 'orange' : 'green';
      parts.push(`<span style="color:white;">${label}</span>: <span style="color:${valueColor};">${val}</span>`);
    }
    el.innerHTML = parts.join('  ');
  };

  const updatePingStats = async () => {
    const targets = [
      { name: 'baidu', host: 'baidu.com' },
      { name: 'aliyun', host: 'aliyun.com' },
      { name: 'tencent', host: '119.29.29.29' },
      { name: 'google', host: 'google.com' },
      { name: 'youtube', host: 'youtube.com' },
      { name: 'bilibili', host: 'bilibili.com' },
    ];
    const pingOne = async (host) => {
      try {
        const cmd = `ping -c 1 -W 2 ${host} 2>/dev/null | grep -o 'time=[0-9.]* ms' | head -1 | cut -d'=' -f2 | cut -d' ' -f1`;
        const res = await run(cmd, 3000);
        const val = res.content.trim();
        if (val && !isNaN(parseFloat(val))) {
          return parseFloat(val).toFixed(0) + 'ms';
        }
        return '超时';
      } catch (e) {
        return '超时';
      }
    };
    const results = await Promise.all(targets.map(t => pingOne(t.host)));
    state.ping.baidu = results[0];
    state.ping.aliyun = results[1];
    state.ping.tencent = results[2];
    state.ping.google = results[3];
    state.ping.youtube = results[4];
    state.ping.bilibili = results[5];
    renderPingDisplay();
  };

  const startAutoRefresh = () => {
    if (state.autoRefreshTimer) {
      clearInterval(state.autoRefreshTimer);
      state.autoRefreshTimer = null;
    }
    state.autoRefresh = true;
    state.autoRefreshTimer = setInterval(() => {
      if (!document.querySelector(`#${PANEL_ID}`)) {
        stopAutoRefresh();
        return;
      }
      loadLog();
      updatePingStats();
      fetchConnectedTime();
    }, 3000);
    const btn = document.querySelector('#bb_toggle_auto');
    if (btn) {
      btn.textContent = '◆ 暂停';
      btn.style.color = '#9dffbf';
    }
  };
  const stopAutoRefresh = () => {
    if (state.autoRefreshTimer) {
      clearInterval(state.autoRefreshTimer);
      state.autoRefreshTimer = null;
    }
    state.autoRefresh = false;
    const btn = document.querySelector('#bb_toggle_auto');
    if (btn) {
      btn.textContent = '▶ 自动';
      btn.style.color = '';
    }
  };

  const toggleCollapse = () => {
    state.collapsed = !state.collapsed;
    const content = document.querySelector('#bb_collapse_content');
    const btn = document.querySelector('#bb_collapse_btn');
    if (content) {
      if (state.collapsed) {
        content.style.height = '0px';
        content.style.overflow = 'hidden';
        if (btn) btn.textContent = '△';
      } else {
        content.style.height = 'auto';
        content.style.overflow = 'visible';
        if (btn) btn.textContent = '▽';
      }
    }
  };

  const refreshAll = async (silent = true, retries = 3) => {
    if (!silent) createToast('刷新状态...', 'pink');
    setBusy(true);
    try {
      for (let attempt = 1; attempt <= retries; attempt++) {
        try {
          await Promise.all([
            readStatus(),
            loadLog(),
            updatePingStats(),
            fetchConnectedTime()
          ]);
          updateUI();
          if (!silent) createToast('已刷新', 'green');
          return;
        } catch (e) {
          if (attempt === retries) throw e;
          await new Promise(resolve => setTimeout(resolve, 500 * attempt));
        }
      }
    } catch (e) {
      createToast('刷新失败', 'red');
    } finally {
      setBusy(false);
    }
  };

  const forceRepairService = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return false; }
    setBusy(true);
    createToast('正在安装/修复...', 'pink');
    try {
      await killAll();
      const writeCmd = `
        mkdir -p ${shellQuote(LOG_DIR)}
        printf '%s' '${BUILTIN_SCRIPT_BASE64}' | base64 -d > ${shellQuote(USER_SERVICE_SH)}
        sed -i 's/\\r$//' ${shellQuote(USER_SERVICE_SH)} 2>/dev/null
        chmod 755 ${shellQuote(USER_SERVICE_SH)}
        cp -f ${shellQuote(USER_SERVICE_SH)} ${shellQuote(SERVICE_SH)}
        chmod 755 ${shellQuote(SERVICE_SH)}
        touch ${shellQuote(LOG_FILE)}
        chmod 666 ${shellQuote(LOG_FILE)}
        touch ${shellQuote(INSTALLED_FLAG)}
      `;
      const res = await run(writeCmd, 10000);
      if (!res.ok) {
        createToast('写入脚本失败', 'red');
        return false;
      }
      const startRes = await run(`sh ${shellQuote(SERVICE_SH)} start`, 10000);
      if (startRes.ok && startRes.content.includes('started')) {
        createToast('安装成功，服务已启动', 'green');
        await refreshAll(true);
        return true;
      } else {
        const errMsg = startRes.content ? startRes.content.slice(0, 200) : '无输出（可能权限或语法错误）';
        createToast('启动失败: ' + errMsg, 'red');
        return false;
      }
    } catch (e) {
      createToast('安装异常: ' + e.message, 'red');
      return false;
    } finally {
      setBusy(false);
    }
  };

  // ----- 自定义帮助模态框（替换 alert） -----
  const showHelp = () => {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.7);
      backdrop-filter: blur(4px);
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      animation: bb_fadeIn 0.3s;
    `;
    // 添加淡入动画
    const style = document.createElement('style');
    style.textContent = `
      @keyframes bb_fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes bb_scaleIn {
        from { transform: scale(0.9); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
      }
    `;
    overlay.appendChild(style);

    const panel = document.createElement('div');
    panel.style.cssText = `
      max-width: 600px;
      width: 100%;
      max-height: 80vh;
      overflow-y: auto;
      background: rgba(20,30,40,0.95);
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.12);
      padding: 24px 28px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.8);
      color: #c8d6e5;
      font-size: 0.85rem;
      line-height: 1.6;
      animation: bb_scaleIn 0.25s;
      position: relative;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '✕';
    closeBtn.style.cssText = `
      position: absolute;
      top: 12px;
      right: 16px;
      background: none;
      border: none;
      color: #aaa;
      font-size: 1.2rem;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 6px;
      transition: background 0.2s;
    `;
    closeBtn.onmouseover = () => { closeBtn.style.background = 'rgba(255,255,255,0.1)'; };
    closeBtn.onmouseout = () => { closeBtn.style.background = 'transparent'; };
    closeBtn.onclick = () => { overlay.remove(); };
    panel.appendChild(closeBtn);

    const content = document.createElement('div');
    content.innerHTML = `
      <h3 style="margin:0 0 12px 0; color:#9dffbf; font-weight:600;">📖 断网自动重启基带守护 - 帮助</h3>
      <div style="white-space:pre-wrap; word-break:break-word;">
本脚本为断网守护脚本
启动后将持续24小时进行域名检测。
如发生断网行为。则将自动重启基带。
重启基带行为只会发生在满足以下条件之一：
1.域名检测网络联通失败超过5次
2.基带网络注册在线时长超过12小时
每次重启基带后，将有1小时的锁定时长。

⚠️ 因作者所在地区常会因某种未知原因长时间基带在网会导致无网，只能重启基带后解决。很麻烦。
所以结合ai制作此脚本。使用本脚本。
作者不承担设备损坏的风险。请谨慎使用！
目前此脚本已稳定在u30air/b26版本上使用两个月。更新迭代至v5.1。已经趋于稳定，故此投稿。

按钮功能说明：
🔧 首次安装/修复 - 使用内置稳定脚本覆盖安装，一键部署。
📤 更新脚本 - 上传自定义 .sh 脚本覆盖。
▶ 启动 / ⏹ 停止 / ⟳ 重启 - 服务控制。
⚡ 手动重启基带 - 立即发送 AT+CFUN=1,1。
📊 日志区 - 自动/手动刷新，清空日志。
      </div>
    `;
    panel.appendChild(content);

    overlay.appendChild(panel);
    // 点击遮罩关闭
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.remove();
    });
    document.body.appendChild(overlay);
  };

  const uploadScript = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.sh';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      setBusy(true);
      createToast('上传中...', 'pink');
      try {
        const text = await file.text();
        const encoded = btoa(unescape(encodeURIComponent(text)));
        await run(`
          mkdir -p ${shellQuote(LOG_DIR)}
          printf '%s' '${encoded}' | base64 -d > ${shellQuote(USER_SERVICE_SH)}
          chmod 755 ${shellQuote(USER_SERVICE_SH)}
        `, 10000);
        createToast('上传成功，正在安装...', 'green');
        await killAll();
        await run(`
          cp -f ${shellQuote(USER_SERVICE_SH)} ${shellQuote(SERVICE_SH)}
          chmod 755 ${shellQuote(SERVICE_SH)}
          touch ${shellQuote(LOG_FILE)}
          chmod 666 ${shellQuote(LOG_FILE)}
          touch ${shellQuote(INSTALLED_FLAG)}
        `, 10000);
        const startRes = await run(`sh ${shellQuote(SERVICE_SH)} start`, 10000);
        if (startRes.ok && startRes.content.includes('started')) {
          createToast('启动成功', 'green');
        } else {
          createToast('启动失败，请检查脚本', 'red');
        }
        await refreshAll(true);
      } catch (err) {
        createToast('上传失败', 'red');
      } finally {
        setBusy(false);
      }
    };
    setTimeout(() => input.click(), 100);
  };

  const startService = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    setBusy(true);
    try {
      await killAll();
      const r = await run(`sh ${shellQuote(SERVICE_SH)} start`, 10000);
      if (r.ok && r.content.includes('started')) {
        createToast('启动成功', 'green');
      } else {
        createToast('启动失败: ' + (r.content || '无输出'), 'red');
      }
      await refreshAll(true);
    } catch (e) {
      createToast('启动异常: ' + e.message, 'red');
    } finally {
      setBusy(false);
    }
  };

  const stopService = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    setBusy(true);
    try {
      const r = await run(`sh ${shellQuote(SERVICE_SH)} stop`, 10000);
      if (r.ok && r.content.includes('已停止')) {
        createToast('已停止', 'green');
      } else {
        await killAll();
        createToast('已强制停止', 'green');
      }
      await refreshAll(true);
    } catch (e) {
      createToast('停止异常: ' + e.message, 'red');
    } finally {
      setBusy(false);
    }
  };

  const restartService = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    setBusy(true);
    try {
      await run(`sh ${shellQuote(SERVICE_SH)} restart`, 10000);
      createToast('重启指令已发送', 'green');
      await refreshAll(true);
    } catch (e) {
      createToast('重启异常: ' + e.message, 'red');
    } finally {
      setBusy(false);
    }
  };

  const manualRestartBaseband = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    const key = 'baseband_manual_confirm';
    if (!sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, '1');
      createToast('再点一次确认发送 AT+CFUN=1,1', 'pink');
      setTimeout(() => sessionStorage.removeItem(key), 3000);
      return;
    }
    sessionStorage.removeItem(key);
    setBusy(true);
    createToast('发送基带重启指令...', 'pink');
    try {
      const r = await run(`curl -s "${API_BASE}/api/AT?command=AT%2BCFUN%3D1%2C1&slot=0"`, 10000);
      if (r.content && r.content.includes('OK')) {
        createToast('基带重启指令已发送', 'green');
        await run(`echo "$(date '+%Y-%m-%d %H:%M:%S') [手动] 通过 /api/AT 执行基带重启" >> ${shellQuote(LOG_FILE)}`, 3000);
        await refreshAll(true);
      } else {
        createToast('发送失败: ' + (r.content || '无响应'), 'red');
      }
    } catch (e) {
      createToast('执行异常: ' + e.message, 'red');
    } finally {
      setBusy(false);
    }
  };

  const toggleBoot = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    if (!state.installed) { createToast('请先安装服务', 'pink'); return; }
    setBusy(true);
    try {
      if (state.bootEnabled) {
        const escaped = BOOT_LINE.replace(/\//g,'\\/').replace(/&/g,'\\&');
        await run(`sed -i '\\#^${escaped}$#d' ${shellQuote(BOOT_SH)}`, 10000);
        await run(`rm -f ${shellQuote(BOOT_FLAG)}`);
        createToast('已取消自启', 'green');
      } else {
        await run(`touch ${shellQuote(BOOT_SH)} && grep -qxF ${shellQuote(BOOT_LINE)} ${shellQuote(BOOT_SH)} || echo ${shellQuote(BOOT_LINE)} >> ${shellQuote(BOOT_SH)}`, 10000);
        await run(`touch ${shellQuote(BOOT_FLAG)}`);
        createToast('已设置自启', 'green');
      }
      await refreshAll(true);
    } catch (e) {
      createToast('切换失败: ' + e.message, 'red');
    } finally {
      setBusy(false);
    }
  };

  const clearLog = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    setBusy(true);
    try {
      await run(`
        mkdir -p ${shellQuote(LOG_DIR)}
        chmod 666 ${shellQuote(LOG_FILE)} 2>/dev/null
        echo -n > ${shellQuote(LOG_FILE)}
      `, 5000);
      await loadLog();
      updateUI();
      createToast('日志已清空', 'green');
    } catch (e) {
      createToast('清空失败: ' + e.message, 'red');
    } finally {
      setBusy(false);
    }
  };

  const uninstallService = async () => {
    if (!(await checkAdvancedFunc())) { createToast('请先启用高级功能', 'pink'); return; }
    const key = 'baseband_uninstall_confirm';
    const btn = document.querySelector('#bb_uninstall_btn');
    if (!sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, '1');
      if (btn) btn.textContent = '⚠️ 再点确认卸载';
      createToast('再点一次确认卸载', 'pink');
      setTimeout(() => {
        sessionStorage.removeItem(key);
        if (btn) btn.textContent = '卸载';
      }, 3000);
      return;
    }
    sessionStorage.removeItem(key);
    if (btn) btn.textContent = '卸载中...';
    setBusy(true);
    createToast('卸载中...', 'pink');
    try {
      await run(`
        sh ${shellQuote(SERVICE_SH)} stop 2>/dev/null
        rm -rf ${shellQuote(BASE_DIR)}
        sed -i '/kano_restart_baseband/d' ${shellQuote(BOOT_SH)}
      `, 15000);
      createToast('卸载完成', 'green');
      stopAutoRefresh();
      await refreshAll(true);
    } catch (e) {
      createToast('卸载异常: ' + e.message, 'red');
    } finally {
      setBusy(false);
      if (btn) btn.textContent = '卸载';
    }
  };

  const setBusy = (busy) => {
    state.busy = busy;
    const root = document.querySelector(`#${PANEL_ID}`);
    if (!root) return;
    root.querySelectorAll('button, textarea, input').forEach(el => { el.disabled = busy; });
  };

  const updateUI = () => {
    const root = document.querySelector(`#${PANEL_ID}`);
    if (!root) return;
    const miniStatus = root.querySelector('#bb_status_mini');
    const dot = root.querySelector('#bb_status_dot');
    if (miniStatus) {
      if (!state.installed) {
        miniStatus.textContent = '○ 未安装';
        miniStatus.style.color = '#888';
        if (dot) { dot.className = 'bb-status-dot'; dot.style.background = '#888'; }
      } else if (state.serviceRunning) {
        miniStatus.textContent = '● 运行中';
        miniStatus.style.color = '#52ef58';
        if (dot) { dot.className = 'bb-status-dot green'; dot.style.background = '#52ef58'; }
      } else {
        miniStatus.textContent = '○ 已停止';
        miniStatus.style.color = '#888';
        if (dot) { dot.className = 'bb-status-dot'; dot.style.background = '#888'; }
      }
    }
    const statusEl = root.querySelector('#bb_status');
    const bootEl = root.querySelector('#bb_boot_status');
    const uploadStatus = root.querySelector('#bb_upload_status');
    const timeEl = root.querySelector('#bb_log_time');
    if (statusEl) {
      if (!state.installed) {
        statusEl.textContent = '未安装';
        statusEl.className = 'bb-chip bad';
      } else {
        statusEl.textContent = state.serviceRunning ? '运行中' : '已停止';
        statusEl.className = `bb-chip ${state.serviceRunning ? 'good' : 'warn'}`;
      }
    }
    if (bootEl) {
      bootEl.textContent = state.bootEnabled ? '已开启' : '未开启';
      bootEl.className = `bb-chip ${state.bootEnabled ? 'good' : 'warn'}`;
    }
    if (uploadStatus) {
      uploadStatus.textContent = state.hasUserScript ? '已检测到脚本' : '请上传 service.sh';
      uploadStatus.style.color = state.hasUserScript ? '#9dffbf' : '#ffaaaa';
    }
    if (timeEl) timeEl.textContent = '刷新: ' + state.refreshedAt;
    renderPingDisplay();
  };

  const render = () => `
    <style>
      #${PANEL_ID} { width:100%; padding:0; margin:2px 0 0 0; box-sizing:border-box; font-family:inherit; }
      #${PANEL_ID} * { box-sizing:border-box; }
      #${PANEL_ID} .bb-panel {
        border-radius: 10px; border: 1px solid rgba(255,255,255,.08);
        background: rgba(255,255,255,.035); backdrop-filter: blur(10px);
        padding: 4px 6px;
        width:100%;
        box-sizing:border-box;
      }
      #${PANEL_ID} .bb-log-area pre {
        width: 100%;
        box-sizing: border-box;
        min-height: 70px;
        max-height: 140px;
        padding: 3px 4px;
        border-radius: 8px;
        border: none;
        background: transparent;
        color: #c8d6e5;
        font-size: .5rem;
        font-family: monospace;
        line-height: 1.5;
        resize: vertical;
        overflow: auto;
        outline: none;
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
      #${PANEL_ID} .bb-log-bar {
        display: flex; justify-content: space-between; align-items: center;
        gap: 3px; margin-bottom: 2px; flex-wrap: wrap;
      }
      #${PANEL_ID} .bb-log-bar .bb-tip { font-size: .5rem; opacity: .7; }
      #${PANEL_ID} .bb-tip { font-size: .5rem; line-height: 1.4; opacity: .8; }
      #${PANEL_ID} .bb-title {
        display: flex; align-items: center; gap: 3px; cursor: pointer;
        user-select: none;
        flex-wrap: wrap;
      }
      #${PANEL_ID} .bb-title strong { font-size: .7rem; }
      #${PANEL_ID} .bb-title small { font-size: .5rem; opacity: .5; font-weight:400; }
      #${PANEL_ID} .bb-title .bb-badge {
        font-size: .45rem; padding: 1px 6px; border-radius: 999px;
        background: rgba(255,255,255,.08);
        font-weight: 400;
      }
      #${PANEL_ID} .bb-ping-display {
        font-size: .45rem;
        opacity: .7;
        margin: 0 2px;
        white-space: normal;
      }
      #${PANEL_ID} .bb-collapse-content {
        overflow: hidden; transition: height 0.25s ease;
        height: 0px;
      }
      #${PANEL_ID} .bb-actions { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 3px; }
      #${PANEL_ID} .bb-actions button { font-size: .55rem; padding: 2px 6px; }
      #${PANEL_ID} .bb-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 3px; margin-bottom: 3px; }
      #${PANEL_ID} .bb-stat-label { font-size: .5rem; opacity: .7; margin-bottom: 1px; }
      #${PANEL_ID} .bb-stat-value { font-size: .65rem; font-weight: 700; }
      #${PANEL_ID} .bb-chip {
        display: inline-flex; padding: 1px 6px; border-radius: 999px;
        font-size: .5rem; font-weight: 700; background: rgba(255,255,255,.08);
      }
      #${PANEL_ID} .bb-chip.good { color: #9dffbf; background: rgba(60,201,120,.16); }
      #${PANEL_ID} .bb-chip.warn { color: #ffd08a; background: rgba(255,173,51,.16); }
      #${PANEL_ID} .bb-chip.bad { color: #ffaaaa; background: rgba(255,80,80,.16); }
      #${PANEL_ID} .bb-file-upload { display: flex; gap: 3px; align-items: center; flex-wrap: wrap; margin-bottom: 2px; }
      #${PANEL_ID} .bb-auto-btn { font-size: .45rem !important; padding: 1px 6px !important; }
      #${PANEL_ID} .bb-cp-btn { font-size: .45rem !important; padding: 1px 6px !important; }
      #${PANEL_ID} .bb-status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
        transition: background-color 0.3s;
        background: #888;
      }
      #${PANEL_ID} .bb-status-dot.green { background: #52ef58; box-shadow: 0 0 4px rgba(82,239,88,0.4); }
      #${PANEL_ID} #bb_log_time_mini { font-size: .5rem !important; }
      #${PANEL_ID} #bb_log_time { font-size: .45rem !important; }
      #${PANEL_ID} #bb_collapse_btn { font-size: .5rem !important; padding: 1px 6px !important; }
      @media (max-width: 720px) {
        #${PANEL_ID} .bb-grid { grid-template-columns: 1fr; }
        #${PANEL_ID} .bb-title { gap: 2px; }
        #${PANEL_ID} .bb-ping-display { font-size: .4rem; }
      }
    </style>
    <div id="${PANEL_ID}">
      <div class="bb-panel" style="padding:3px 6px;">
        <div class="bb-title" id="bb_title_click">
          <span class="bb-status-dot" id="bb_status_dot"></span>
          <strong>📡 断网重启基带守护服务</strong>
          <small>v5.1</small>
          <span class="bb-badge" id="bb_status_mini">● 就绪</span>
          <span class="bb-ping-display" id="bb_ping_display">百度: -  阿里: -  腾讯: -  谷歌: -  油管: -  Bili: -</span>
          <span style="margin-left:auto;font-size:.5rem;opacity:.7;" id="bb_log_time_mini">已连接: --</span>
          <button id="bb_collapse_btn" style="font-size:.5rem;padding:1px 6px;"> △ </button>
        </div>
      </div>
      <div class="bb-collapse-content" id="bb_collapse_content">
        <div class="bb-panel" style="margin-top:2px;">
          <div class="bb-grid">
            <div>
              <div class="bb-stat-label">服务状态</div>
              <div class="bb-stat-value"><span class="bb-chip" id="bb_status">读取中</span></div>
            </div>
            <div>
              <div class="bb-stat-label">开机自启动</div>
              <div class="bb-stat-value"><span class="bb-chip" id="bb_boot_status">读取中</span></div>
            </div>
          </div>
          <div class="bb-file-upload">
            <button id="bb_repair_btn" style="background:rgba(255,200,0,0.2);color:#ffd700;">🔧 首次安装/修复</button>
            <button id="bb_upload_btn">📤 更新脚本</button>
            <span id="bb_upload_status" style="font-size:.5rem;">检测中...</span>
          </div>
          <div class="bb-actions">
            <button id="bb_start_btn">▶ 启动服务</button>
            <button id="bb_stop_btn">⏹ 停止服务</button>
            <button id="bb_restart_btn">⟳ 重启服务</button>
            <button id="bb_manual_restart_btn" style="background:rgba(255,170,70,.15);color:#ffd08a;">⚡ 手动重启基带</button>
            <button id="bb_toggle_boot_btn">设置自启</button>
            <button id="bb_uninstall_btn">卸载</button>
            <button id="bb_refresh_btn">刷新</button>
            <button id="bb_help_action" style="background:rgba(100,200,255,0.15);color:#8fcbff;">❓ 帮助</button>
          </div>
          <div class="bb-tip" style="margin-top:2px;font-size:.45rem;opacity:.5;">
            💡 首次使用请点击「首次安装/修复」一键部署；也可上传自定义脚本。
          </div>
        </div>
      </div>
      <div class="bb-panel" style="margin-top:2px;">
        <div class="bb-log-bar">
          <span class="bb-tip">&nbsp;&nbsp;⚅ 运行日志（最近100行）</span>
          <span style="font-size:.45rem;opacity:.5;" id="bb_log_time">刷新: --</span>
          <div style="display:flex;gap:2px;align-items:center;">
            <button id="bb_toggle_auto" class="bb-auto-btn">▶ 自动</button>
            <button id="bb_refresh_log_btn" class="bb-cp-btn">刷新</button>
            <button id="bb_clear_log_btn" class="bb-cp-btn">清空</button>
          </div>
        </div>
        <div class="bb-log-area">
          <pre id="bb_log_text">（暂无日志）</pre>
        </div>
      </div>
    </div>
  `;

  const injectPanel = () => {
    const oldPanel = document.querySelector(`#${PANEL_ID}`);
    if (oldPanel) oldPanel.remove();
    const container = document.querySelector(CONTAINER_SELECTOR);
    if (!container) {
      setTimeout(injectPanel, 500);
      return;
    }
    container.insertAdjacentHTML('afterend', render());
    bindEvents();
    const content = document.querySelector('#bb_collapse_content');
    if (content) {
      content.style.height = '0px';
      content.style.overflow = 'hidden';
    }
    refreshAll(true);
    startAutoRefresh();
  };

  const bindEvents = () => {
    const root = document.querySelector(`#${PANEL_ID}`);
    if (!root) return;

    root.querySelector('#bb_collapse_btn').onclick = toggleCollapse;
    root.querySelector('#bb_title_click').onclick = (e) => {
      if (e.target.closest('button')) return;
      toggleCollapse();
    };
    root.querySelector('#bb_help_action').onclick = showHelp;
    root.querySelector('#bb_repair_btn').onclick = forceRepairService;
    root.querySelector('#bb_upload_btn').onclick = uploadScript;
    root.querySelector('#bb_start_btn').onclick = startService;
    root.querySelector('#bb_stop_btn').onclick = stopService;
    root.querySelector('#bb_restart_btn').onclick = restartService;
    root.querySelector('#bb_manual_restart_btn').onclick = manualRestartBaseband;
    root.querySelector('#bb_toggle_boot_btn').onclick = toggleBoot;
    root.querySelector('#bb_uninstall_btn').onclick = uninstallService;
    root.querySelector('#bb_refresh_btn').onclick = () => refreshAll(false);
    root.querySelector('#bb_refresh_log_btn').onclick = loadLog;
    root.querySelector('#bb_clear_log_btn').onclick = clearLog;
    root.querySelector('#bb_toggle_auto').onclick = () => {
      if (state.autoRefresh) {
        stopAutoRefresh();
      } else {
        startAutoRefresh();
      }
    };
  };

  const init = () => {
    if (document.querySelector(CONTAINER_SELECTOR)) {
      injectPanel();
    } else {
      const observer = new MutationObserver(() => {
        if (document.querySelector(CONTAINER_SELECTOR)) {
          observer.disconnect();
          injectPanel();
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(() => {
        observer.disconnect();
        if (!document.querySelector(`#${PANEL_ID}`)) {
          injectPanel();
        }
      }, 5000);
    }
  };

  init();
})();
//</script>