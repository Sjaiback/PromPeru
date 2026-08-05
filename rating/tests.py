from io import BytesIO
from django.test import SimpleTestCase
from openpyxl import Workbook
from .views import leer_excel


class ExcelParserTests(SimpleTestCase):
    def test_lee_encabezados_multinivel_y_filas(self):
        wb = Workbook()
        ws = wb.active
        ws.merge_cells("A5:A7")
        ws["A5"] = "RUC"
        ws.merge_cells("B5:C5")
        ws["B5"] = "Información Básica"
        ws["B6"] = "Razón Social"
        ws["C6"] = "Sector"
        ws["B7"] = "Valor"
        ws["C7"] = "Valor"
        ws.append([])
        ws["A8"] = "20123456789"
        ws["B8"] = "Empresa"
        ws["C8"] = "Servicios"
        out = BytesIO()
        wb.save(out)
        headers, rows = leer_excel(out.getvalue(), 5, 3)
        self.assertIn("RUC", headers[0])
        self.assertIn("Razón Social", headers[1])
        self.assertEqual(rows[0][0], "20123456789")
