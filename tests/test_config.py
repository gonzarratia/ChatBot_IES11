# -*- coding: utf-8 -*-
"""Tests de configuración y de la regla de dependencias del paquete (ies_bot/config.py)."""
import os
import subprocess
import sys
import unittest
from datetime import timedelta

import ayudas  # noqa: F401  (agrega la raíz del proyecto al path)
from ies_bot import config

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


class TestHoraLocal(unittest.TestCase):
    def test_zona_argentina_utc_menos_3(self):
        self.assertEqual(config.ahora_local().utcoffset(), timedelta(hours=-3))


class TestRutas(unittest.TestCase):
    def test_logo_se_busca_en_la_raiz_del_proyecto_junto_a_app_py(self):
        # El paquete vive en ies_bot/ pero el logo está un nivel más arriba, junto a app.py.
        self.assertEqual(os.path.abspath(str(config.RUTA_LOGO.parent)), RAIZ)
        self.assertEqual(config.RUTA_LOGO.name, "logo_ies11_round.png")


class TestCapasPuras(unittest.TestCase):
    def test_config_bot_ia_y_privacidad_no_importan_streamlit_ni_gspread(self):
        """Regla de arquitectura: la lógica se prueba sin Streamlit ni Google instalados."""
        codigo = ("import sys, ies_bot.config, ies_bot.privacidad, ies_bot.bot, ies_bot.ia; "
                  "malos = [m for m in ('streamlit', 'gspread') if m in sys.modules]; "
                  "sys.exit(','.join(malos) if malos else 0)")
        r = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
