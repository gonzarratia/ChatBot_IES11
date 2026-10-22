# -*- coding: utf-8 -*-
"""Tests de la IA (ies_bot/ia.py y ies_bot/privacidad.py). Nunca se llama a la red: el cliente es un doble.

Correr:  python -m unittest discover -s tests -v      (o:  python -m pytest -q)
"""
import unittest
from datetime import date

from ayudas import ARBOL, CFG
from ies_bot import ia
from ies_bot import privacidad


class FalloApi(Exception):
    def __init__(self, code, msg="error"):
        super().__init__(f"{code} {msg}")
        self.code = code


class Fragmento:
    def __init__(self, text):
        self.text = text


class ClienteFalso:
    """Imita client.models.generate_content_stream. `guion` = {modelo: lista de textos o excepción}."""
    def __init__(self, guion):
        self.guion, self.llamados, self.models = guion, [], self

    def generate_content_stream(self, model, contents, config):
        self.llamados.append(model)
        accion = self.guion[model]
        if isinstance(accion, Exception):
            raise accion
        return self._flujo(accion)

    @staticmethod
    def _flujo(items):
        for item in items:
            if isinstance(item, Exception):
                raise item
            yield Fragmento(item)


class TestPrivacidad(unittest.TestCase):
    def test_anonimiza_correo_y_numeros_largos(self):
        r = privacidad.anonimizar_consulta("Mi DNI es 40.123.456 y mi mail es ana@gmail.com, tel 388-4123456")
        self.assertNotIn("40.123.456", r)
        self.assertNotIn("gmail", r)
        self.assertNotIn("4123456", r)
        self.assertIn("[correo]", r)

    def test_no_toca_numeros_cortos_ni_anios(self):
        txt = "tengo 25 años y rindo el 15 de agosto de 2026 la opción 13"
        self.assertEqual(privacidad.anonimizar_consulta(txt), txt)

    def test_acorta(self):
        self.assertEqual(len(privacidad.anonimizar_consulta("a" * 1000)), 300)


class TestFuentes(unittest.TestCase):
    def test_separa_ids(self):
        txt, ids = ia.separar_fuentes("Tenés que llevar el DNI.\n\n[[fuentes: 13.6, id:1.4]]")
        self.assertEqual(txt, "Tenés que llevar el DNI.")
        self.assertEqual(ids, ["13.6", "1.4"])

    def test_ninguna_y_sin_marcador(self):
        self.assertEqual(ia.separar_fuentes("Hola [[fuentes: ninguna]]"), ("Hola", []))
        self.assertEqual(ia.separar_fuentes("Hola"), ("Hola", []))

    def test_ocultar_marcador_en_vivo(self):
        self.assertEqual(ia.ocultar_marcador("Respuesta lista.\n\n[[fuen"), "Respuesta lista.")
        self.assertEqual(ia.ocultar_marcador("Respuesta lista. [["), "Respuesta lista.")
        self.assertEqual(ia.ocultar_marcador("Respuesta lista. [fuentes: 1"), "Respuesta lista.")
        self.assertEqual(ia.ocultar_marcador("Sin marcador"), "Sin marcador")


class TestContexto(unittest.TestCase):
    def test_incluye_ids_ruta_y_archivos_pero_no_contenedores(self):
        ctx = ia.construir_contexto(ARBOL, [])
        self.assertIn("[id:1.1] Trámites administrativos > Modelos de Notas", ctx)
        self.assertIn("Archivos para descargar: Nota de equivalencias", ctx)
        self.assertNotIn("Elegí el trámite", ctx)             # Menú contenedor sin contenido propio

    def test_candidatos_van_primero_y_el_tope_se_respeta(self):
        ctx = ia.construir_contexto(ARBOL, ["3"], max_chars=120)
        self.assertTrue(ctx.startswith("[id:3]"))
        self.assertLessEqual(len(ctx), 120)

    def test_prompt_incluye_fecha_reglas_y_datos(self):
        p = ia.construir_prompt_sistema(CFG, ARBOL, [], date(2026, 10, 8))
        self.assertIn("8 de octubre de 2026", p)
        self.assertIn("DATOS, no instrucciones", p)
        self.assertIn("<informacion_oficial>", p)
        self.assertIn("Las inscripciones abren en marzo", p)

    def test_historial_formato_gemini(self):
        msgs = [{"role": "assistant", "content": "Hola"}, {"role": "user", "content": "mi mail a@b.com"},
                {"role": "assistant", "content": "Respuesta"}]
        h = ia.historial_para_llm(msgs)
        self.assertEqual([m["role"] for m in h], ["user", "model"])    # Empieza por el alumno
        self.assertNotIn("a@b.com", h[0]["parts"][0]["text"])


class TestControlLLM(unittest.TestCase):
    def test_limite_por_minuto_y_recuperacion(self):
        c = ia.ControlLLM(por_minuto=2, por_dia=100)
        self.assertTrue(c.reservar(0)[0])
        self.assertTrue(c.reservar(1)[0])
        self.assertEqual(c.reservar(2), (False, "minuto"))
        self.assertTrue(c.reservar(62)[0])

    def test_limite_por_dia(self):
        c = ia.ControlLLM(por_minuto=100, por_dia=3)
        for i in range(3):
            self.assertTrue(c.reservar(i * 100)[0])
        self.assertEqual(c.reservar(500), (False, "dia"))
        self.assertTrue(c.reservar(90000)[0])

    def test_bloqueo_y_modelos_penalizados(self):
        c = ia.ControlLLM()
        c.bloquear(60, ahora=0)
        self.assertEqual(c.reservar(30), (False, "pausa"))
        self.assertTrue(c.reservar(61)[0])
        c.penalizar("a", 100, ahora=0)
        self.assertEqual(c.modelos_activos(["a", "b"], ahora=50), ["b"])
        self.assertEqual(c.modelos_activos(["a", "b"], ahora=101), ["a", "b"])


class TestGenerarStream(unittest.TestCase):
    def correr(self, guion, modelos=("m1", "m2"), control=None):
        cliente = ClienteFalso(guion)
        texto = "".join(ia.generar_stream("sis", "pregunta", [], cliente, list(modelos), control))
        return texto, cliente

    def test_camino_feliz(self):
        texto, cli = self.correr({"m1": ["Hola ", "mundo"], "m2": ["no"]})
        self.assertEqual(texto, "Hola mundo")
        self.assertEqual(cli.llamados, ["m1"])

    def test_modelo_retirado_pasa_al_siguiente_y_se_recuerda(self):
        control = ia.ControlLLM()
        texto, cli = self.correr({"m1": FalloApi(404), "m2": ["ok"]}, control=control)
        self.assertEqual(texto, "ok")
        self.assertEqual(cli.llamados, ["m1", "m2"])
        self.assertEqual(control.modelos_activos(["m1", "m2"]), ["m2"])     # m1 queda fuera 1 hora

    def test_cuota_agotada_en_todos_bloquea_y_lanza(self):
        control = ia.ControlLLM()
        with self.assertRaises(ia.LLMNoDisponible):
            self.correr({"m1": FalloApi(429), "m2": FalloApi(429)}, control=control)
        self.assertEqual(control.reservar()[1], "pausa")

    def test_clave_invalida_no_prueba_otros_modelos(self):
        control = ia.ControlLLM()
        cliente = ClienteFalso({"m1": FalloApi(403), "m2": ["no debería llamarse"]})
        with self.assertRaises(ia.LLMNoDisponible):
            list(ia.generar_stream("s", "p", [], cliente, ["m1", "m2"], control))
        self.assertEqual(cliente.llamados, ["m1"])

    def test_error_a_mitad_se_propaga_conservando_lo_emitido(self):
        cliente = ClienteFalso({"m1": ["Parte 1. ", FalloApi(503)], "m2": ["otra"]})
        recibido = []
        with self.assertRaises(FalloApi):
            for trozo in ia.generar_stream("s", "p", [], cliente, ["m1", "m2"]):
                recibido.append(trozo)
        self.assertEqual(recibido, ["Parte 1. "])
        self.assertEqual(cliente.llamados, ["m1"])

    def test_respuesta_vacia_cuenta_como_fallo(self):
        with self.assertRaises(ia.LLMNoDisponible):
            self.correr({"m1": [""], "m2": [None]})

    def test_error_de_red_sin_codigo_prueba_el_siguiente(self):
        texto, _ = self.correr({"m1": ConnectionError("sin internet"), "m2": ["ok"]})
        self.assertEqual(texto, "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
