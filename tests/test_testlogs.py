from pcbrag import testlogs
from pcbrag.config import ROOT

LOG = """=== CTRL-BRD FUNCTIONAL TEST ===
serial: CB-24-99999
board: CTRL-BRD rev C
pcb_lot: L2406
[08:00:01] STEP 01 rail_3v3              3.291 V   lim 3.200..3.400   PASS
[08:00:02] STEP 02 uart_loopback             -                          FAIL (timeout after 500 ms)
result: FAIL
"""


def test_parse_single_log():
    rec = testlogs.parse(LOG, "x.log")
    assert rec["serial"] == "CB-24-99999"
    assert rec["result"] == "FAIL"
    assert rec["steps"][0]["value"] == 3.291
    assert rec["steps"][1]["status"] == "FAIL"
    assert "timeout" in rec["steps"][1]["note"]


def test_summary_mentions_failed_step():
    text = testlogs.summarize(testlogs.parse(LOG, "x.log"))
    assert "Failed steps: uart_loopback" in text


def test_stats_on_sample_logs():
    s = testlogs.stats(testlogs.parse_dir(ROOT / "data" / "test_logs"))
    assert "40 boards tested" in s
    assert "uart_loopback: 4" in s
