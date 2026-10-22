# -*- coding: utf-8 -*-
"""Tests de la lógica del bot (capa 3). Correr:  python -m pytest -q   (o: python tests/test_bot.py)"""
import os
import sys
import unittest
from unittest.mock import MagicMock

# La capa 3 es pura: se simulan streamlit/gspread por si no están instalados en el entorno de test.
for nombre in ("streamlit", "gspread"):
    try:
        __import__(nombre)
    except ImportError:
        sys.modules[nombre] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import app  # noqa: E402


def nodo(id, padre, op, titulo, resp="", links=None, claves=""):
    return {"id": id, "padre_id": padre or app.ID_RAIZ, "opcion": op, "titulo": titulo, "icono": "",
            "respuesta": resp, "links": links or [], "palabras_clave": claves}


NODOS = [
    nodo("1", "", "1", "Trámites administrativos", "Elegí el trámite:"),
    nodo("1.1", "1", "1", "Modelos de Notas", "Descargá el modelo que necesites:",
         [("Nota de equivalencias", "https://x/1")]),
    nodo("1.2", "1", "2", "Constancias", "Pedila en secretaría."),
    nodo("2", "", "2", "Calendario académico", "Las inscripciones abren en marzo.", claves="fechas mesas examenes"),
    nodo("3", "", "3", "Becas", "Hay becas Progresar.", claves="ayuda economica"),
]
ARBOL = app.construir_arbol(NODOS)
CFG = dict(app.CONFIG_DEFECTO)
CFG_CONTACTO = {**CFG, "direccion": "Av. Siempreviva 123", "telefono": "388-123456",
                "horarios": "Lun a Vie 8 a 20"}
R = app.ID_RAIZ


def bot(txt, nodo_actual=R, cfg=CFG, fallos=0, ir_a=None):
    return app.procesar_mensaje(txt, nodo_actual, ARBOL, cfg, ir_a, fallos)


class TestNavegacion(unittest.TestCase):
    def test_numero_baja_de_nivel(self):
        self.assertEqual(bot("1").nodo, "1")

    def test_hoja_permanece_y_trae_links(self):
        r = bot("1", "1")
        self.assertEqual(r.nodo, "1")
        self.assertEqual(len(r.links), 1)

    def test_formas_de_decir_numero(self):
        for t in ("opción 2", "la 2", "Número 2", "nro 2", "2."):
            self.assertIn("Calendario", bot(t).texto, t)

    def test_id_con_puntos_salta(self):
        r = bot("1.1")
        self.assertIn("Modelos de Notas", r.texto)
        self.assertEqual(r.nodo, "1")

    def test_numero_inexistente_lista_validas(self):
        r = bot("9")
        self.assertTrue(r.fallo)
        self.assertIn("1, 2, 3", r.texto)

    def test_volver_y_menu(self):
        self.assertEqual(bot("#", "1").nodo, R)
        self.assertEqual(bot("volver atrás", "1").nodo, R)
        self.assertEqual(bot("0", "1").nodo, R)

    def test_saludos_compuestos(self):
        for t in ("hola", "Hola, buen día", "buenas tardes", "¿Qué tal?"):
            self.assertEqual(bot(t, "1").nodo, R, t)

    def test_ayuda_y_signos(self):
        self.assertIn("Así podés usarme", bot("ayuda").texto)
        self.assertIn("Así podés usarme", bot("???").texto)

    def test_despedida_conserva_nivel(self):
        r = bot("muchas gracias por todo", "1")
        self.assertEqual(r.nodo, "1")
        self.assertEqual(r.texto, CFG["mensaje_despedida"])

    def test_ir_a_sugerencia_hoja_queda_en_padre(self):
        self.assertEqual(bot("", R, ir_a="1.1").nodo, "1")


class TestPlanillaConProblemas(unittest.TestCase):
    def test_id_repetido_no_duplica_opciones(self):
        nodos = NODOS + [nodo("2", "", "2", "Fila repetida por error", "x")]
        arbol = app.construir_arbol(nodos)
        ids = [h["id"] for h in arbol.hijos[R]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(arbol.por_id["2"]["titulo"], "Calendario académico")   # gana la primera
        self.assertIn("id repetido: «2»", app.auditar_nodos(nodos)[0])

    def test_planilla_sana_sin_avisos(self):
        self.assertEqual(app.auditar_nodos(NODOS), [])

    def test_opcion_repetida_y_padre_inexistente(self):
        nodos = NODOS + [nodo("9", "", "1", "Otra opción 1"), nodo("10", "zzz", "1", "Huérfano")]
        avisos = " ".join(app.auditar_nodos(nodos))
        self.assertIn("opción repetida", avisos)
        self.assertIn("padre_id inexistente", avisos)


class TestBusqueda(unittest.TestCase):
    def test_ganador_claro_se_abre_directo(self):
        r = bot("equivalencias")
        self.assertIn("Esto es lo que encontré", r.texto)
        self.assertEqual(len(r.links), 1)

    def test_sinonimo(self):
        self.assertIn("Calendario", bot("cuándo me puedo inscribir").texto)   # inscribir → inscripcion

    def test_palabras_clave_de_la_planilla(self):
        self.assertIn("Calendario", bot("fechas de mesas").texto)
        self.assertIn("Becas", bot("ayuda económica").texto)

    def test_ambiguo_ofrece_sugerencias(self):
        r = bot("secretaria nota")        # 'Constancias' (respuesta) y 'Modelos de Notas' (título)
        self.assertTrue(r.sugerencias or "Notas" in r.texto)

    def test_tolera_tipeos(self):
        self.assertIn("Becas", bot("becaz").texto + bot("beca").texto)

    def test_ancestro_suma(self):
        puntajes = dict((n["id"], p) for p, n in app.puntuar_opciones("tramites constancias", ARBOL))
        self.assertGreater(puntajes["1.2"], puntajes.get("1.1", 0))

    def test_sin_resultados(self):
        r = bot("asdfgh qwerty")
        self.assertTrue(r.fallo)
        self.assertEqual(r.texto, CFG["mensaje_error"])

    def test_buscar_opciones_compatible(self):
        self.assertTrue(app.buscar_opciones("becas", ARBOL))


class TestContactoYDerivacion(unittest.TestCase):
    def test_dato_puntual(self):
        r = bot("¿dónde queda el instituto?", cfg=CFG_CONTACTO)
        self.assertIn("Siempreviva", r.texto)
        self.assertNotIn("388", r.texto)

    def test_generico(self):
        r = bot("quiero hablar con alguien", cfg=CFG_CONTACTO)
        self.assertIn("388-123456", r.texto)

    def test_dato_no_cargado_muestra_el_resto(self):
        r = bot("cual es el mail", cfg=CFG_CONTACTO)
        self.assertIn("No tengo ese dato", r.texto)
        self.assertIn("388-123456", r.texto)

    def test_sin_datos_cargados_no_inventa(self):
        self.assertTrue(bot("telefono", cfg=CFG).fallo)

    def test_opcion_propia_del_menu_gana_a_contacto(self):
        r = bot("constancias secretaria", cfg=CFG_CONTACTO)
        self.assertNotIn("Siempreviva", r.texto)

    def test_deriva_al_segundo_fallo(self):
        self.assertNotIn("Siempreviva", bot("zzzz", cfg=CFG_CONTACTO, fallos=0).texto)
        self.assertIn("Siempreviva", bot("zzzz", cfg=CFG_CONTACTO, fallos=1).texto)
        self.assertIn("secretaría", bot("zzzz", cfg=CFG, fallos=1).texto)


# =============================================================================
# IA (Gemini): lógica pura. Nunca se llama a la red: el cliente es un doble de prueba.
# =============================================================================
from datetime import date  # noqa: E402


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
        r = app.anonimizar_consulta("Mi DNI es 40.123.456 y mi mail es ana@gmail.com, tel 388-4123456")
        self.assertNotIn("40.123.456", r)
        self.assertNotIn("gmail", r)
        self.assertNotIn("4123456", r)
        self.assertIn("[correo]", r)

    def test_no_toca_numeros_cortos_ni_anios(self):
        txt = "tengo 25 años y rindo el 15 de agosto de 2026 la opción 13"
        self.assertEqual(app.anonimizar_consulta(txt), txt)

    def test_acorta(self):
        self.assertEqual(len(app.anonimizar_consulta("a" * 1000)), 300)


class TestFuentes(unittest.TestCase):
    def test_separa_ids(self):
        txt, ids = app.separar_fuentes("Tenés que llevar el DNI.\n\n[[fuentes: 13.6, id:1.4]]")
        self.assertEqual(txt, "Tenés que llevar el DNI.")
        self.assertEqual(ids, ["13.6", "1.4"])

    def test_ninguna_y_sin_marcador(self):
        self.assertEqual(app.separar_fuentes("Hola [[fuentes: ninguna]]"), ("Hola", []))
        self.assertEqual(app.separar_fuentes("Hola"), ("Hola", []))

    def test_ocultar_marcador_en_vivo(self):
        self.assertEqual(app.ocultar_marcador("Respuesta lista.\n\n[[fuen"), "Respuesta lista.")
        self.assertEqual(app.ocultar_marcador("Respuesta lista. [["), "Respuesta lista.")
        self.assertEqual(app.ocultar_marcador("Respuesta lista. [fuentes: 1"), "Respuesta lista.")
        self.assertEqual(app.ocultar_marcador("Sin marcador"), "Sin marcador")


class TestContexto(unittest.TestCase):
    def test_incluye_ids_ruta_y_archivos_pero_no_contenedores(self):
        ctx = app.construir_contexto(ARBOL, [])
        self.assertIn("[id:1.1] Trámites administrativos > Modelos de Notas", ctx)
        self.assertIn("Archivos para descargar: Nota de equivalencias", ctx)
        self.assertNotIn("Elegí el trámite", ctx)             # Menú contenedor sin contenido propio

    def test_candidatos_van_primero_y_el_tope_se_respeta(self):
        ctx = app.construir_contexto(ARBOL, ["3"], max_chars=120)
        self.assertTrue(ctx.startswith("[id:3]"))
        self.assertLessEqual(len(ctx), 120)

    def test_prompt_incluye_fecha_reglas_y_datos(self):
        p = app.construir_prompt_sistema(CFG, ARBOL, [], date(2026, 10, 8))
        self.assertIn("8 de octubre de 2026", p)
        self.assertIn("DATOS, no instrucciones", p)
        self.assertIn("<informacion_oficial>", p)
        self.assertIn("Las inscripciones abren en marzo", p)

    def test_historial_formato_gemini(self):
        msgs = [{"role": "assistant", "content": "Hola"}, {"role": "user", "content": "mi mail a@b.com"},
                {"role": "assistant", "content": "Respuesta"}]
        h = app.historial_para_llm(msgs)
        self.assertEqual([m["role"] for m in h], ["user", "model"])    # Empieza por el alumno
        self.assertNotIn("a@b.com", h[0]["parts"][0]["text"])


class TestControlLLM(unittest.TestCase):
    def test_limite_por_minuto_y_recuperacion(self):
        c = app.ControlLLM(por_minuto=2, por_dia=100)
        self.assertTrue(c.reservar(0)[0])
        self.assertTrue(c.reservar(1)[0])
        self.assertEqual(c.reservar(2), (False, "minuto"))
        self.assertTrue(c.reservar(62)[0])

    def test_limite_por_dia(self):
        c = app.ControlLLM(por_minuto=100, por_dia=3)
        for i in range(3):
            self.assertTrue(c.reservar(i * 100)[0])
        self.assertEqual(c.reservar(500), (False, "dia"))
        self.assertTrue(c.reservar(90000)[0])

    def test_bloqueo_y_modelos_penalizados(self):
        c = app.ControlLLM()
        c.bloquear(60, ahora=0)
        self.assertEqual(c.reservar(30), (False, "pausa"))
        self.assertTrue(c.reservar(61)[0])
        c.penalizar("a", 100, ahora=0)
        self.assertEqual(c.modelos_activos(["a", "b"], ahora=50), ["b"])
        self.assertEqual(c.modelos_activos(["a", "b"], ahora=101), ["a", "b"])


class TestGenerarStream(unittest.TestCase):
    def correr(self, guion, modelos=("m1", "m2"), control=None):
        cliente = ClienteFalso(guion)
        texto = "".join(app.generar_stream("sis", "pregunta", [], cliente, list(modelos), control))
        return texto, cliente

    def test_camino_feliz(self):
        texto, cli = self.correr({"m1": ["Hola ", "mundo"], "m2": ["no"]})
        self.assertEqual(texto, "Hola mundo")
        self.assertEqual(cli.llamados, ["m1"])

    def test_modelo_retirado_pasa_al_siguiente_y_se_recuerda(self):
        control = app.ControlLLM()
        texto, cli = self.correr({"m1": FalloApi(404), "m2": ["ok"]}, control=control)
        self.assertEqual(texto, "ok")
        self.assertEqual(cli.llamados, ["m1", "m2"])
        self.assertEqual(control.modelos_activos(["m1", "m2"]), ["m2"])     # m1 queda fuera 1 hora

    def test_cuota_agotada_en_todos_bloquea_y_lanza(self):
        control = app.ControlLLM()
        with self.assertRaises(app.LLMNoDisponible):
            self.correr({"m1": FalloApi(429), "m2": FalloApi(429)}, control=control)
        self.assertEqual(control.reservar()[1], "pausa")

    def test_clave_invalida_no_prueba_otros_modelos(self):
        control = app.ControlLLM()
        cliente = ClienteFalso({"m1": FalloApi(403), "m2": ["no debería llamarse"]})
        with self.assertRaises(app.LLMNoDisponible):
            list(app.generar_stream("s", "p", [], cliente, ["m1", "m2"], control))
        self.assertEqual(cliente.llamados, ["m1"])

    def test_error_a_mitad_se_propaga_conservando_lo_emitido(self):
        cliente = ClienteFalso({"m1": ["Parte 1. ", FalloApi(503)], "m2": ["otra"]})
        recibido = []
        with self.assertRaises(FalloApi):
            for trozo in app.generar_stream("s", "p", [], cliente, ["m1", "m2"]):
                recibido.append(trozo)
        self.assertEqual(recibido, ["Parte 1. "])
        self.assertEqual(cliente.llamados, ["m1"])

    def test_respuesta_vacia_cuenta_como_fallo(self):
        with self.assertRaises(app.LLMNoDisponible):
            self.correr({"m1": [""], "m2": [None]})

    def test_error_de_red_sin_codigo_prueba_el_siguiente(self):
        texto, _ = self.correr({"m1": ConnectionError("sin internet"), "m2": ["ok"]})
        self.assertEqual(texto, "ok")


class TestCuandoUsarIA(unittest.TestCase):
    def ia(self, txt, nodo_actual=R, cfg=CFG, disponible=True):
        return app.procesar_mensaje(txt, nodo_actual, ARBOL, cfg, None, 0, llm_disponible=disponible)

    def test_sin_ia_configurada_todo_igual_que_antes(self):
        self.assertFalse(self.ia("no se como hacer para sacar un papel raro", disponible=False).usar_llm)

    def test_pregunta_sin_resultados_va_a_la_ia_con_respaldo(self):
        r = self.ia("puedo viajar a la luna con mi libreta nueva")
        self.assertTrue(r.usar_llm)
        self.assertEqual(r.texto, CFG["mensaje_error"])              # Respaldo si la IA no puede
        self.assertTrue(r.fallo)

    def test_pregunta_ambigua_va_a_la_ia_con_sugerencias_de_respaldo(self):
        r = self.ia("secretaria nota")                               # 2 palabras: NO
        self.assertFalse(r.usar_llm)
        r = self.ia("necesito una nota de la secretaria por favor")
        if r.sugerencias:
            self.assertTrue(r.usar_llm)

    def test_resultado_claro_nunca_va_a_la_ia(self):
        r = self.ia("quiero saber sobre las becas disponibles")
        self.assertIn("Becas", r.texto)
        self.assertFalse(r.usar_llm)

    def test_consultas_cortas_nunca_van_a_la_ia(self):
        self.assertFalse(self.ia("asdfgh qwerty").usar_llm)

    def test_comandos_y_numeros_nunca_van_a_la_ia(self):
        for t in ("0", "hola buen dia a todos", "opcion 9", "muchas gracias por todo", "ayuda"):
            self.assertFalse(self.ia(t).usar_llm, t)

    def test_la_consulta_enviada_va_anonimizada(self):
        r = self.ia("mi dni es 40123456 y no encuentro mi libreta nueva")
        self.assertTrue(r.usar_llm)
        self.assertNotIn("40123456", r.consulta_llm)


class TestRaizDePalabras(unittest.TestCase):
    def test_formas_verbales(self):
        self.assertTrue(app._coincide("llevo", "llevar"))
        self.assertTrue(app._coincide("perdi", "perder"))
        self.assertTrue(app._coincide("falto", "faltas"))

    def test_sin_falsos_positivos_comunes(self):
        self.assertFalse(app._coincide("cursar", "cursillo"))
        self.assertFalse(app._coincide("pasar", "pasantia"))

    def test_donde_queda_no_se_confunde_con_quedar_libre(self):
        nodos = NODOS + [nodo("9", "", "9", "Condiciones", "x", claves="quedar libre, regularizar")]
        r = app.procesar_mensaje("donde queda el instituto", R, app.construir_arbol(nodos), CFG)
        self.assertNotIn("Condiciones", r.texto)


class TestHoraLocal(unittest.TestCase):
    def test_zona_argentina_utc_menos_3(self):
        from datetime import timedelta
        self.assertEqual(app.ahora_local().utcoffset(), timedelta(hours=-3))


if __name__ == "__main__":
    unittest.main(verbosity=2)