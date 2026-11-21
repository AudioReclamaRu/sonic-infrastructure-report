"""Regression tests for legacy GEO answer disposition safety."""
from __future__ import annotations
import copy
import json
import unittest
from tools.legacy_geo_answer_disposition import MATRIX,PROVENANCE,ROUTES,validate


class TestLegacyGeoAnswerDisposition(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.matrix=json.loads(MATRIX.read_text(encoding="utf-8"))
  cls.provenance=json.loads(PROVENANCE.read_text(encoding="utf-8"))
  cls.routes=json.loads(ROUTES.read_text(encoding="utf-8"))

 def test_all_legacy_pages_have_a_valid_disposition(self):
  self.assertEqual(validate(self.matrix,self.provenance,self.routes),[])

 def test_missing_legacy_page_is_rejected(self):
  data=copy.deepcopy(self.matrix);data["pages"].pop()
  self.assertTrue(any("cover exactly all legacy pages" in x for x in validate(data,self.provenance,self.routes)))

 def test_unknown_professional_route_is_rejected(self):
  data=copy.deepcopy(self.matrix);data["pages"][0]["professional_route_ids"]=["not-a-route"]
  self.assertTrue(any("unknown route ids" in x for x in validate(data,self.provenance,self.routes)))

 def test_immediate_redirect_is_rejected(self):
  data=copy.deepcopy(self.matrix);data["pages"][0]["redirect_or_retire"]="redirect_now"
  self.assertTrue(any("must defer irreversible action" in x for x in validate(data,self.provenance,self.routes)))

 def test_audio_plus_eligibility_gate_must_remain_explicit(self):
  data=copy.deepcopy(self.matrix);data["pages"][0]["audio_plus_path"]=""
  self.assertTrue(any("must preserve eligibility gate" in x for x in validate(data,self.provenance,self.routes)))

 def test_old_offer_publication_date_is_preserved(self):
  data=copy.deepcopy(self.matrix);data["source_freshness"]["offer"]["visible_publication_date"]="2026-11-21"
  self.assertTrue(any("publication date must remain visible" in x for x in validate(data,self.provenance,self.routes)))

 def test_paid_edit_and_contractual_correction_remain_unresolved(self):
  data=copy.deepcopy(self.matrix);data["source_freshness"]["correction_terms"]["status"]="resolved"
  self.assertTrue(any("interpretation_not_resolved" in x for x in validate(data,self.provenance,self.routes)))

 def test_video_voiceover_offer_scope_remains_unresolved(self):
  data=copy.deepcopy(self.matrix);data["source_freshness"]["scope_difference"]["status"]="confirmed"
  self.assertTrue(any("scope difference must remain unresolved" in x for x in validate(data,self.provenance,self.routes)))

 def test_all_urls_stay_stable_until_page_level_evidence(self):
  data=copy.deepcopy(self.matrix);data["summary"]["recommended_keep_urls"]=6
  self.assertTrue(any("all seven URLs" in x for x in validate(data,self.provenance,self.routes)))


if __name__=="__main__": unittest.main()
