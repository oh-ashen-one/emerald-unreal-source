import datetime,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from engine_launch_budget import update,LaunchBudgetExceeded

class EngineLaunchBudgetTests(unittest.TestCase):
    def test_tenth_admitted_eleventh_denied_then_window_expires(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);now=datetime.datetime(2026,11,14,tzinfo=datetime.timezone.utc)
            for i in range(10):self.assertTrue(update(root,admit='owned-engine',now=now+datetime.timedelta(seconds=i))['can_launch'])
            with self.assertRaises(LaunchBudgetExceeded):update(root,admit='eleventh',now=now+datetime.timedelta(seconds=10))
            self.assertEqual(update(root,now=now+datetime.timedelta(seconds=10))['count_last_hour'],10)
            self.assertTrue(update(root,admit='after-window',now=now+datetime.timedelta(hours=1,milliseconds=1))['can_launch'])
    def test_seeds_prior_receipts_once_without_foreign_or_duplicate_starts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'out').mkdir();now=datetime.datetime(2026,11,14,tzinfo=datetime.timezone.utc)
            row={'cwd':str(root),'label':'emerald-test','started_at':now.isoformat(),'pid':20}
            for name in ('gpu-one.json','gpu-duplicate.json'):(root/'out'/name).write_text(json.dumps(row))
            (root/'out/gpu-foreign.json').write_text(json.dumps(dict(row,cwd='/another-project')))
            self.assertEqual(update(root,now=now)['count_last_hour'],1)
            update(root,admit='new-native',now=now+datetime.timedelta(seconds=1))
            self.assertEqual(update(root,now=now+datetime.timedelta(seconds=2))['count_last_hour'],2)
    def test_read_only_check_does_not_consume_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for _ in range(3):self.assertEqual(update(root)['count_last_hour'],0)
    def test_backwards_clock_does_not_erase_recent_admissions(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);now=datetime.datetime(2026,11,14,tzinfo=datetime.timezone.utc)
            update(root,admit='owned-engine',now=now)
            self.assertEqual(update(root,now=now-datetime.timedelta(minutes=5))['count_last_hour'],1)
