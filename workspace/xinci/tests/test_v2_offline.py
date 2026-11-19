import os, sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, "/workspace/xinci")
from v2.metrics import parse_semrush_overview_csv, parse_missing_as_nodata, 立项_status, classify_replication
from v2.budget import Ledger
from v2.select_keywords import select_board_keywords
from v2.snapshots import sitemap_diff, report_is_current

class TestV2Offline(unittest.TestCase):
    def test_semrush_missing_is_not_zero(self):
        text = "Keyword;Search Volume;CPC;Competition;Number of Results\r\ngpts;5400;0.14;0.24;122\r\nzeroed;0;0.01;0.1;10\r\n"
        parsed = parse_semrush_overview_csv(text)
        assert parsed['gpts']['volume']==5400 and parsed['gpts']['nodata'] is False
        assert parsed['zeroed']['volume']==0 and parsed['zeroed']['nodata'] is False
        miss = parse_missing_as_nodata(['gpts','absent','zeroed'], parsed)
        assert 'absent' in miss
        assert miss['absent']['nodata'] is True
        assert miss['absent']['volume'] is None

    def test_budget_unpriced_denied_and_prior(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf_path = tf.name
        try:
            ledger = Ledger(path=tf_path, date='2026-11-19', hard_cap_usd=1.0, today_prior_usd=0.3)
            assert abs(ledger.remaining_usd - 0.7) < 1e-6
            assert ledger.allows(None) is False
            assert ledger.allows(0.8) is False
            assert ledger.allows(0.2) is True
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_video_quota_not_squeezed(self):
        entries = []
        for i in range(4):
            entries.append({'phrase': f'v_{i}', 'source': '热梗轨', 'names': 'n', 'evidence': 'e'})
        for i in range(30):
            entries.append({'phrase': f'g_{i}', 'source': '游戏轨', 'names': 'n', 'evidence': 'e'})
        for i in range(30):
            entries.append({'phrase': f'a_{i}', 'source': 'AI工具轨', 'names': 'n', 'evidence': 'e'})
        
        res = select_board_keywords(entries)
        video = [e for e in res if e['source']=='热梗轨']
        games = [e for e in res if e['source']=='游戏轨']
        assert len(video) >= 4
        assert len(games) <= 10
        assert len(res) <= 40
        assert len(video) != 0

    def test_game_reserve_not_padded(self):
        entries = []
        for i in range(2):
            entries.append({'phrase': f'g_{i}', 'source': '游戏轨', 'names': 'n', 'evidence': 'e'})
        for i in range(5):
            entries.append({'phrase': f'v_{i}', 'source': '热梗轨', 'names': 'n', 'evidence': 'e'})
        
        res = select_board_keywords(entries)
        games = [e for e in res if e['source']=='游戏轨']
        assert len(games) == 2

    def test_sitemap_first_run_new_zero(self):
        diff = sitemap_diff(None, {'a', 'b'})
        assert diff.get('first_run') is True
        assert diff.get('new_count', len(diff.get('new', []))) == 0

    def test_sitemap_second_run_only_new(self):
        diff = sitemap_diff({'a', 'b'}, {'a', 'b', 'c'})
        assert list(diff.get('new', [])) == ['c']

    def test_replication_same_caption_not_independent(self):
        res1 = classify_replication([
            {'author': 'a1', 'caption': 'hello world', 'video_verified': False},
            {'author': 'a2', 'caption': 'hello world', 'video_verified': False},
        ])
        assert res1['independent_ugc'] is False
        assert res1['video_semantics'] == '未核实'

        res2 = classify_replication([
            {'author': 'a1', 'caption': 'hello world', 'video_verified': True},
            {'author': 'a2', 'caption': 'hello world', 'video_verified': True},
        ])
        assert res2['independent_ugc'] is False

    def test_expired_report(self):
        assert report_is_current({}, '2026-11-19') is False
        assert report_is_current({'date': '2026-11-19'}, '2026-11-19') is True

    def test_立项_nodata_not_fail_volume(self):
        st = 立项_status(None, None, None, True)
        assert st['status'] == '待验证'
        assert st['passed_立项'] is False

if __name__ == '__main__':
    unittest.main()
