"""No-network tests for KALE's separated regulator registry."""
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import regulatory_core as core
from tools.regulatory_sync import fda_label_to_row, generic_row, read_xlsx

class RegulatoryTests(unittest.TestCase):
    def setUp(self):
        self.work=tempfile.TemporaryDirectory()
        self.db=Path(self.work.name)/"regulatory.sqlite3"
        self.conn=core.open_writer(self.db)
    def tearDown(self):
        self.conn.close()
        self.work.cleanup()

    def test_all_nine_agencies_are_registered(self):
        self.assertEqual(len(core.AGENCIES),9)
        self.assertIn("TITCK",core.AGENCIES)
        self.assertIn("WHO",core.AGENCIES)

    def test_official_url_disallows_fake_domains(self):
        self.assertEqual(core.official_url("TITCK","https://titck.gov.tr.evil.invalid/a"),"")
        self.assertEqual(core.official_url("FDA","http://api.fda.gov/a"),"")
        self.assertTrue(core.official_url("EMA","https://www.ema.europa.eu/en/medicines"))
        self.assertEqual(core.official_url("WHO","https://other.invalid/a"),"")

    def test_do_not_touch_primary_med_catalog(self):
        primary=Path(self.work.name)/"kale.db"
        primary.write_bytes(b"existing user data")
        core.write_record(self.conn,regulator="FDA",source_id="label-1",
                          name="TEST BRAND",ingredients="Amoxicillin",
                          url="https://open.fda.gov/apis/drug/label/",imported_at="2026-11-07")
        self.conn.commit()
        self.assertEqual(primary.read_bytes(),b"existing user data")

    def test_duplicate_source_does_not_grow(self):
        for x in (1,2):
            core.write_record(self.conn,regulator="FDA",source_id="label-1",
                              name="TEST BRAND",ingredients="Amoxicillin",
                              status="Label only",imported_at="2026-11-07")
        self.conn.commit()
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],1)
        with patch.object(core,"DB",self.db):
            self.assertEqual(len(core.search_products("amoxicillin")),1)
            item=core.get_product("FDA","label-1")
            self.assertIn("disclaimer",item)

    def test_no_false_equivalence_or_empty_results(self):
        with patch.object(core,"DB",self.db):
            self.assertEqual(core.search_products("a"),[])
            self.assertEqual(core.get_product("FAKE","x"),None)
            self.assertEqual(core.stats()["total"],0)

    def test_fda_label_approval_is_not_inferred(self):
        sample={"set_id":"12345", "effective_time":"20261001",
                "openfda":{"brand_name":["TEST BRAND"],"generic_name":["AMOXICILLIN"]},
                "indications_and_usage":["Official English label text"]}
        row=fda_label_to_row(sample)
        self.assertEqual(row["regulator"],"FDA")
        self.assertIn("doğrulanmadı",row["status"])
        self.assertEqual(row["sections"]["indications_and_usage"],"Official English label text")

    def test_ema_export_column_recognition(self):
        row=generic_row({"Product short name":"Aspirin Example",
               "Active Substance":"ACETYLSALICYLIC ACID",
               "Country of authorisation":"Germany","Marketing authorisation number":"EU/1/11/123"},
               "EMA")
        self.assertEqual(row["name"],"Aspirin Example")
        self.assertEqual(row["source_id"],"EU/1/11/123")
        self.assertIn("ACETYLSALICYLIC",row["ingredients"])

    def test_minimal_xlsx_reader(self):
        xml=("<?xml version='1.0' encoding='UTF-8'?>"
            "<worksheet xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'>"
            "<sheetData><row r='1'><c r='A1' t='inlineStr'><is><t>Product name</t></is></c>"
            "<c r='B1' t='inlineStr'><is><t>Active substance</t></is></c>"
            "<c r='C1' t='inlineStr'><is><t>Country</t></is></c></row>"
            "<row r='2'><c r='A2' t='inlineStr'><is><t>Test med</t></is></c>"
            "<c r='B2' t='inlineStr'><is><t>Ingredient</t></is></c>"
            "<c r='C2' t='inlineStr'><is><t>UK</t></is></c></row></sheetData></worksheet>")
        path=Path(self.work.name)/"sample.xlsx"
        with zipfile.ZipFile(path,"w") as z:
            z.writestr("xl/worksheets/sheet1.xml",xml)
        rows=list(read_xlsx(path))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["Product name"],"Test med")

if __name__=="__main__":
    unittest.main()
