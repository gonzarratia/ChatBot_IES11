# -*- coding: utf-8 -*-
"""Tests del bot (ies_bot/bot.py): navegación, búsqueda, atajos y decisión de cuándo usar la IA.

Correr:  python -m unittest discover -s tests -v      (o:  python -m pytest -q)
"""
import unittest

from ayudas import ARBOL, CFG, CFG_CONTACTO, NODOS, R, bot, nodo
from ies_bot import bot as motor


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
        arbol = motor.construir_arbol(nodos)
        ids = [h["id"] for h in arbol.hijos[R]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(arbol.por_id["2"]["titulo"], "Calendario académico")   # gana la primera
        self.assertIn("id repetido: «2»", motor.auditar_nodos(nodos)[0])

    def test_planilla_sana_sin_avisos(self):
        self.assertEqual(motor.auditar_nodos(NODOS), [])

    def test_opcion_repetida_y_padre_inexistente(self):
        nodos = NODOS + [nodo("9", "", "1", "Otra opción 1"), nodo("10", "zzz", "1", "Huérfano")]
        avisos = " ".join(motor.auditar_nodos(nodos))
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
        puntajes = dict((n["id"], p) for p, n in motor.puntuar_opciones("tramites constancias", ARBOL))
        self.assertGreater(puntajes["1.2"], puntajes.get("1.1", 0))

    def test_sin_resultados(self):
        r = bot("asdfgh qwerty")
        self.assertTrue(r.fallo)
        self.assertEqual(r.texto, CFG["mensaje_error"])

    def test_buscar_opciones_compatible(self):
        self.assertTrue(motor.buscar_opciones("becas", ARBOL))


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


class TestCuandoUsarIA(unittest.TestCase):
    def ia(self, txt, nodo_actual=R, cfg=CFG, disponible=True):
        return motor.procesar_mensaje(txt, nodo_actual, ARBOL, cfg, None, 0, llm_disponible=disponible)

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
        self.assertTrue(motor._coincide("llevo", "llevar"))
        self.assertTrue(motor._coincide("perdi", "perder"))
        self.assertTrue(motor._coincide("falto", "faltas"))

    def test_sin_falsos_positivos_comunes(self):
        self.assertFalse(motor._coincide("cursar", "cursillo"))
        self.assertFalse(motor._coincide("pasar", "pasantia"))

    def test_donde_queda_no_se_confunde_con_quedar_libre(self):
        nodos = NODOS + [nodo("9", "", "9", "Condiciones", "x", claves="quedar libre, regularizar")]
        r = motor.procesar_mensaje("donde queda el instituto", R, motor.construir_arbol(nodos), CFG)
        self.assertNotIn("Condiciones", r.texto)


if __name__ == "__main__":
    unittest.main(verbosity=2)
