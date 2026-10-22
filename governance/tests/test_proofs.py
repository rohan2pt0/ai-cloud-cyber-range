"""./securax proofs (governance/proofs.py): reads the status lights and the journeys without running anything, finds the
claims that say "not yet proven", puts those ahead of plans on paper, and names the closest journey only when it really
shares distinctive words."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("securax_proofs_t", ROOT / "governance" / "proofs.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

STATUS = [{"doc": "securax/09-TIERS.md", "light": "red", "text": "A business model on paper; no tiers are built."},
          {"doc": "securax/58-PHONES.md", "light": "amber", "text": "Built and tested: pairing. Not yet verified on a real phone (the sandbox has no second device)."},
          {"doc": "securax/01-OK.md", "light": "green", "text": "Everything proven."}]
JOURNEYS = {"phone_device": "A second device: the Life OS on an emulated phone over HTTPS, offline and synced.",
            "backup_restore": "A backup is taken and restored."}


def test_green_pages_have_no_gaps_and_unproven_claims_come_first():
    out = pf.gaps(STATUS, JOURNEYS, {"phone_device": ["guiding-map"]}, {})
    assert [g["doc"] for g in out] == ["securax/58-PHONES.md", "securax/09-TIERS.md"]
    assert out[0]["kind"] == "unproven" and "real phone" in out[0]["claim"]


def test_the_closest_journey_is_named_only_on_a_real_overlap():
    hit = pf.suggest("Not yet verified on a real phone second device", JOURNEYS, {"phone_device": ["guiding-map"]})
    assert hit["journey"] == "phone_device" and hit["guards"] == ["guiding-map"]
    assert pf.suggest("No certification has been started", JOURNEYS, {})["journey"] is None


def test_it_reads_the_real_repository_without_running_anything():
    items = pf.report()
    assert items and all(i["light"] in ("amber", "red") for i in items)
    assert len(pf.read_journeys(ROOT / "sandbox" / "run.py")) >= 40
