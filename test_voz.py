import pytest
from ies.ia import (transcribir_audio, ControlLLM, LLMNoDisponible, AudioDemasiadoLargo, AUDIO_MAX_BYTES)

class Err(Exception):
    def __init__(self, code): super().__init__(f"{code} error"); self.code = code
class R:
    def __init__(self, text): self.text = text
class Modelos:
    def __init__(self, plan): self.plan, self.llamadas, self.ultimo = plan, [], None
    def generate_content(self, model, contents, config):
        self.llamadas.append(model); self.ultimo = (contents, config)
        r = self.plan[model]
        if isinstance(r, Exception): raise r
        return R(r)
class Cliente:
    def __init__(self, plan): self.models = Modelos(plan)

WAV = b"RIFF" + b"\0" * 1000

def test_transcribe_y_manda_el_audio_inline():
    c = Cliente({"m1": '  "Quiero saber\n sobre becas"  '})
    assert transcribir_audio(WAV, c, ["m1"]) == "Quiero saber sobre becas"
    partes = c.models.ultimo[0][0]["parts"]
    assert partes[1]["inline_data"] == {"mime_type": "audio/wav", "data": WAV}
    assert c.models.ultimo[1]["temperature"] == 0.0

def test_failover_404_pasa_al_siguiente_y_penaliza():
    ctl = ControlLLM(); c = Cliente({"viejo": Err(404), "nuevo": "hola"})
    assert transcribir_audio(WAV, c, ["viejo", "nuevo"], ctl) == "hola"
    assert ctl.modelos_activos(["viejo", "nuevo"]) == ["nuevo"]

def test_sin_voz_devuelve_vacio():
    assert transcribir_audio(WAV, Cliente({"m": "[sin_voz]"}), ["m"]) == ""
    assert transcribir_audio(WAV, Cliente({"m": ""}), ["m"]) == ""
    assert transcribir_audio(b"", Cliente({"m": "x"}), ["m"]) == ""

def test_recorta_a_200_caracteres():
    assert len(transcribir_audio(WAV, Cliente({"m": "a" * 500}), ["m"])) == 200

def test_audio_largo_no_llama_a_la_api():
    c = Cliente({"m": "x"})
    with pytest.raises(AudioDemasiadoLargo): transcribir_audio(b"0" * (AUDIO_MAX_BYTES + 1), c, ["m"])
    assert c.models.llamadas == []

def test_cuota_agotada_lanza_y_bloquea():
    ctl = ControlLLM(); c = Cliente({"m1": Err(429), "m2": Err(429)})
    with pytest.raises(LLMNoDisponible): transcribir_audio(WAV, c, ["m1", "m2"], ctl)
    assert ctl.reservar()[1] == "pausa"        # pausa global de 60 s tras el 429

def test_clave_invalida_no_prueba_otros_modelos():
    c = Cliente({"m1": Err(403), "m2": "no debe llamarse"})
    with pytest.raises(LLMNoDisponible): transcribir_audio(WAV, c, ["m1", "m2"], ControlLLM())
    assert c.models.llamadas == ["m1"]

def test_comparte_el_limite_por_minuto_con_las_respuestas():
    ctl = ControlLLM(por_minuto=1); c = Cliente({"m": "hola"})
    assert transcribir_audio(WAV, c, ["m"], ctl) == "hola"
    with pytest.raises(LLMNoDisponible): transcribir_audio(WAV, c, ["m"], ctl)
