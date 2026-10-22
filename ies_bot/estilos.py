# -*- coding: utf-8 -*-
"""Hoja de estilos (CSS) de la interfaz.

Aislada para poder retocar el diseño sin tocar la lógica de pantalla. Los tokens (colores, radios,
sombras, degradados) están al comienzo en `:root`; el resto del CSS solo los reutiliza.
"""
from __future__ import annotations

ESTILOS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Source+Sans+3:wght@400;600;700&display=swap');

/* ============ Tokens ============ */
:root{
  --navy:#1E2A47; --azul:#2F7BD9; --azul-medio:#2A6BC4; --azul-fuerte:#1F56B8; --celeste:#2BA8E3;
  --fondo-base:#EDF3FC; --niebla:#F3F6FB; --hielo:#EAF3FD; --linea:#D5E2F3; --pizarra:#566580; --verde:#1E9E5A;
  --ambar:#F5A524; --ambar-suave:#FFF4DC; --ambar-linea:#F3D9A0; --ambar-texto:#7A5200;
  --grad-marca:linear-gradient(115deg,#1E2A47 0%,#1F56B8 58%,#2A6BC4 100%);
  --grad-aro:linear-gradient(135deg,#2F7BD9,#2BA8E3);
  --r-sm:10px; --r-md:14px; --r-lg:22px; --r-xl:28px;
  --sombra:0 1px 2px rgba(30,42,71,.06),0 4px 14px rgba(30,42,71,.07);
  --sombra-alta:0 2px 4px rgba(30,42,71,.06),0 12px 28px rgba(31,86,184,.16);
  color-scheme:light;
}

/* ============ Base y fondo ============ */
.stApp,.stMarkdown,.stChatInput textarea,.stButton button{
  font-family:'Source Sans 3','Segoe UI',system-ui,-apple-system,sans-serif;}
.stApp{
  background-color:var(--fondo-base);
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Ccircle cx='200' cy='200' r='150' fill='none' stroke='%232BA8E3' stroke-opacity='.20' stroke-width='46'/%3E%3Ccircle cx='200' cy='200' r='104' fill='none' stroke='%232F7BD9' stroke-opacity='.10' stroke-width='3'/%3E%3Ccircle cx='200' cy='200' r='196' fill='none' stroke='%231E2A47' stroke-opacity='.07' stroke-width='2'/%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400'%3E%3Ccircle cx='200' cy='200' r='150' fill='none' stroke='%232F7BD9' stroke-opacity='.15' stroke-width='40'/%3E%3Ccircle cx='200' cy='200' r='104' fill='none' stroke='%23F5A524' stroke-opacity='.22' stroke-width='3'/%3E%3C/svg%3E"),
    radial-gradient(1100px 640px at 0% 0%,rgba(43,168,227,.30),transparent 60%),
    radial-gradient(900px 600px at 100% 6%,rgba(47,123,217,.18),transparent 62%),
    radial-gradient(900px 640px at 88% 108%,rgba(31,86,184,.18),transparent 62%),
    radial-gradient(760px 520px at 8% 104%,rgba(245,165,36,.15),transparent 62%),
    radial-gradient(rgba(30,42,71,.07) 1px,transparent 1.4px),
    linear-gradient(160deg,#F9FBFF 0%,#EAF2FD 48%,#E9EEFC 100%);
  background-size:580px 580px,480px 480px,auto,auto,auto,auto,24px 24px,auto;
  background-position:right -190px top -170px,left -170px bottom -150px,0 0,0 0,0 0,0 0,0 0,0 0;
  background-repeat:no-repeat,no-repeat,no-repeat,no-repeat,no-repeat,no-repeat,repeat,no-repeat;
  background-attachment:fixed;}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stBottom"]{background:transparent;}
[data-testid="stBottom"]>div{background:linear-gradient(to top,rgba(234,242,253,.97) 58%,rgba(234,242,253,0));}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"]{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:820px;margin:1rem auto 1rem;padding:1.6rem 1.8rem 3.5rem;
  background:linear-gradient(180deg,rgba(255,255,255,.72),rgba(255,255,255,.52));
  backdrop-filter:blur(14px) saturate(140%);
  border:1px solid rgba(255,255,255,.85);border-radius:var(--r-xl);
  box-shadow:0 1px 0 rgba(255,255,255,.9) inset,0 24px 60px rgba(31,86,184,.13),0 2px 6px rgba(30,42,71,.05);}
[data-testid="stElementContainer"]:has(iframe[height="0"]),
[data-testid="stElementContainer"]:has(iframe[srcdoc*="__ies"]){height:0;margin:0;overflow:hidden;position:absolute;}
::selection{background:rgba(43,168,227,.28);}
*{scrollbar-width:thin;scrollbar-color:#B9CBE6 transparent;}

/* ============ Cabecera completa ============ */
div.hero{position:relative;overflow:hidden;display:flex;align-items:center;gap:1.6rem;
  background:var(--grad-marca);border-radius:var(--r-xl);padding:2rem 2.1rem;margin-bottom:1.5rem;
  box-shadow:0 16px 36px rgba(31,86,184,.30);animation:aparecer .5s ease-out both;}
div.hero::before{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:radial-gradient(rgba(255,255,255,.16) 1.3px,transparent 1.6px);background-size:18px 18px;
  mask-image:linear-gradient(100deg,transparent 38%,#000 100%);}
div.hero::after{content:"";position:absolute;right:-64px;top:-84px;width:270px;height:270px;
  border-radius:50%;border:36px solid rgba(43,168,227,.30);box-shadow:0 0 0 44px rgba(255,255,255,.05);pointer-events:none;}
div.hero .hero-marco{position:relative;z-index:1;flex:none;width:98px;height:98px;border-radius:50%;
  background:#fff;padding:5px;box-shadow:0 0 0 5px rgba(255,255,255,.22),0 10px 24px rgba(10,20,50,.35);}
div.hero .hero-logo{display:block;width:100%;height:100%;border-radius:50%;}
div.hero .hero-logo-emoji{display:flex;align-items:center;justify-content:center;font-size:2.5rem;}
div.hero .hero-texto{position:relative;z-index:1;}
div.hero .hero-chip{display:inline-flex;align-items:center;gap:.45rem;margin-bottom:.6rem;
  padding:.2rem .8rem;border-radius:999px;font-size:.88rem;font-weight:600;color:#fff;
  background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.38);}
div.hero .hero-chip::before{content:"";width:.5rem;height:.5rem;border-radius:50%;background:#7CF2B1;
  box-shadow:0 0 0 3px rgba(124,242,177,.28);}
div.stMarkdown div.hero h1{font-family:'Montserrat',sans-serif;font-weight:800;
  font-size:1.7rem;line-height:1.18;letter-spacing:-.01em;color:#fff;margin:0 0 .5rem;padding:0;}
div.stMarkdown div.hero p{margin:0;max-width:56ch;color:#fff;font-size:1.03rem;line-height:1.55;}
div.hero .hero-pistas{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:1rem;}
div.hero .hero-pistas span{padding:.22rem .75rem;border-radius:999px;color:#fff;font-size:.86rem;
  font-weight:600;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.28);}
@keyframes aparecer{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}

/* ============ Cabecera compacta ============ */
div.barra{position:relative;display:flex;align-items:center;gap:.8rem;background:#fff;
  border:1px solid var(--linea);border-radius:var(--r-md);padding:.55rem 1rem .55rem 1.1rem;
  margin-bottom:1rem;box-shadow:var(--sombra);overflow:hidden;}
div.barra::before{content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--grad-aro);}
div.barra img{width:38px;height:38px;border-radius:50%;flex:none;box-shadow:0 0 0 2px #fff,0 0 0 3.5px var(--celeste);}
div.barra .barra-texto{flex:1;min-width:0;}
div.barra .barra-nombre{font-family:'Montserrat',sans-serif;font-weight:700;font-size:.92rem;line-height:1.25;color:var(--navy);}
div.barra .barra-estado{display:flex;align-items:center;gap:.4rem;font-size:.84rem;color:var(--pizarra);}
div.barra .punto{width:.5rem;height:.5rem;border-radius:50%;background:var(--verde);box-shadow:0 0 0 3px rgba(30,158,90,.18);}
div.barra .barra-ia{flex:none;font-size:.8rem;font-weight:700;color:var(--ambar-texto);
  background:var(--ambar-suave);border:1px solid var(--ambar-linea);border-radius:999px;padding:.15rem .65rem;}

/* ============ Mensajes y Burbujas ============ */
/* Solución a los márgenes inferiores comprimidos: padding asimétrico */
[data-testid="stChatMessage"]{background:#fff;border:1px solid var(--linea);
  border-left:4px solid var(--celeste);border-radius:6px var(--r-md) var(--r-md) var(--r-md);
  padding:1.2rem 1.4rem 1.6rem 1.4rem;margin-bottom:.55rem;
  background-image:linear-gradient(180deg,#fff 0%,#F8FBFF 100%);
  box-shadow:0 1px 2px rgba(30,42,71,.05),0 8px 22px rgba(31,86,184,.09);}
[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li{color:var(--navy);line-height:1.6;font-size:1.04rem;}
[data-testid="stChatMessage"] strong{color:var(--azul-fuerte);}
[data-testid="stChatMessage"] a{color:var(--azul-fuerte);font-weight:600;}
[data-testid="stChatMessage"] code{background:var(--hielo);color:var(--azul-fuerte);border-radius:6px;padding:.1rem .35rem;}
[data-testid^="stChatMessageAvatar"]{width:2.6rem;height:2.6rem;border-radius:50%;background:#fff;
  box-shadow:0 0 0 2px #fff,0 0 0 4px var(--celeste),0 6px 14px rgba(43,168,227,.28);}
[data-testid^="stChatMessageAvatar"] img{border-radius:50%;}
.fila-usuario{display:flex;justify-content:flex-end;margin:.9rem .5rem .65rem 0;scroll-margin-top:6.5rem;}
.burbuja-usuario{max-width:82%;color:#fff;padding:.85rem 1.3rem;line-height:1.45;overflow-wrap:anywhere;
  border-radius:var(--r-md) var(--r-md) 4px var(--r-md);
  background:linear-gradient(135deg,var(--azul-medio) 0%,var(--azul-fuerte) 100%);
  box-shadow:0 6px 16px rgba(31,86,184,.28);}

[data-testid="stChatMessage"] [data-testid="stCaptionContainer"]{display:inline-block;margin-top:.7rem;
  background:var(--ambar-suave);border:1px solid var(--ambar-linea);border-radius:var(--r-sm);padding:.35rem .7rem;}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p{color:var(--ambar-texto);font-size:.86rem;line-height:1.4;}

/* Divisor discreto para navegación */
.divisor-nav{text-align:center;margin:1.5rem 0 .5rem;color:var(--pizarra);font-size:.9rem;font-weight:600;}

/* Indicador mientras la IA busca */
.escribiendo{display:inline-flex;align-items:center;gap:.35rem;color:var(--pizarra);font-size:.97rem;}
.escribiendo i{width:.42rem;height:.42rem;border-radius:50%;background:var(--azul);animation:latido 1.2s ease-in-out infinite;}
.escribiendo i:nth-of-type(2){animation-delay:.15s;}
.escribiendo i:nth-of-type(3){animation-delay:.3s;}
@keyframes latido{0%,60%,100%{opacity:.25;}30%{opacity:1;}}

/* ============ Descargas (Acciones) ============ */
/* Solución a los botones sin margen inferior: se inyecta margin-bottom explícito */
.acciones {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1.1rem;
  margin-bottom: 1.2rem !important; /* Asegura el margen inferior dentro de la tarjeta */
  padding-bottom: 0.2rem;
}

a.btn-descarga {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: #fff !important;
  font-weight: 600;
  font-size: 0.97rem;
  text-decoration: none !important;
  padding: 0.62rem 1.15rem;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--azul-medio), var(--azul-fuerte));
  box-shadow: 0 4px 12px rgba(31, 86, 184, 0.26);
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}

a.btn-descarga:hover {
  background: var(--navy);
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(30, 42, 71, 0.30);
}

a.btn-descarga:focus-visible {
  outline: 3px solid rgba(47, 123, 217, 0.5);
  outline-offset: 2px;
}

/* ============ Opciones de respuesta rápida ============ */
.guia{display:flex;align-items:center;gap:.55rem;color:var(--navy);
  font-family:'Montserrat',sans-serif;font-weight:700;font-size:.95rem;margin:1.4rem 0 .75rem;}
.guia::before{content:"";flex:none;width:5px;height:1.15em;border-radius:5px;background:var(--grad-aro);}
.guia.guia-faq{margin-top:.1rem;}
.migas{display:inline-flex;flex-wrap:wrap;align-items:center;gap:.2rem;background:#fff;
  border:1px solid var(--linea);border-left:4px solid var(--celeste);border-radius:999px;
  padding:.3rem 1rem;margin:1.1rem 0 .75rem;color:var(--pizarra);font-size:.92rem;box-shadow:var(--sombra);}
.migas b{color:var(--azul-fuerte);font-weight:700;}

.stButton,[data-testid="stButton"]{width:100%;}
[data-testid="stColumn"]{min-width:0;}
.stButton>button{width:100%;justify-content:flex-start;text-align:left;min-height:3.6rem;
  color:var(--navy);font-weight:600;font-size:1.02rem;line-height:1.3;padding:.7rem 1.1rem;
  background:linear-gradient(180deg,#fff,#F8FBFF);
  border:1px solid var(--linea);border-left:4px solid var(--celeste);border-radius:var(--r-md);
  box-shadow:0 1px 2px rgba(30,42,71,.05),0 6px 16px rgba(31,86,184,.08);
  transition:transform .15s,box-shadow .15s,border-color .15s,background .15s;}
.stButton>button p{margin:0;text-align:left;white-space:normal;}
[data-testid="stColumn"]:nth-child(even) .stButton>button{border-left-color:var(--azul-fuerte);}
.stButton>button:hover{transform:translateY(-2px);box-shadow:var(--sombra-alta);border-color:var(--azul);
  border-left-color:var(--azul-fuerte);background:linear-gradient(90deg,var(--hielo),#fff 75%);color:var(--navy);}
.stButton>button:active{transform:translateY(0);background:#DCEBFB;}
.stButton>button:focus-visible{outline:3px solid rgba(47,123,217,.45);outline-offset:1px;}
.stButton>button[kind="primary"],.st-key-faq .stButton>button{min-height:2.3rem;padding:.3rem .95rem;border-radius:999px;
  justify-content:center;border:1px solid var(--linea);background:#fff;color:var(--azul-fuerte);
  font-size:.94rem;font-weight:600;box-shadow:0 1px 2px rgba(30,42,71,.06),0 3px 8px rgba(31,86,184,.10);}
.stButton>button[kind="primary"] p,.st-key-faq .stButton>button p{text-align:center;}
.stButton>button[kind="primary"]:hover,.st-key-faq .stButton>button:hover{background:var(--hielo);border-color:var(--azul);
  color:var(--azul-fuerte);transform:translateY(-1px);box-shadow:0 6px 14px rgba(31,86,184,.20);}

[class*="st-key-vermas_"]{display:block;width:100% !important;margin:.5rem 0 0;}
[class*="st-key-vermas_"] .stButton>button{width:100%;justify-content:center;min-height:2.8rem;
  border:1px solid var(--linea);background:var(--hielo);color:var(--azul-fuerte);
  font-weight:700;letter-spacing:.01em;box-shadow:0 1px 2px rgba(30,42,71,.05);}
[class*="st-key-vermas_"] .stButton>button p{text-align:center;font-weight:700;}
[class*="st-key-vermas_"] .stButton>button:hover{background:#DCEBFB;border-color:var(--azul);
  transform:none;box-shadow:0 2px 6px rgba(31,86,184,.14);}

/* ============ Barra superior fija ============ */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] .barra){position:sticky;top:.75rem;z-index:60;}
div.barra{background:#fff;box-shadow:0 1px 2px rgba(30,42,71,.06),0 10px 26px rgba(31,86,184,.16);}
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] .barra)::before{content:"";
  position:absolute;z-index:-1;left:-1.2rem;right:-1.2rem;top:-.75rem;bottom:-4rem;pointer-events:none;
  background:linear-gradient(to bottom,var(--fondo-base) 40%,rgba(237,243,252,0) 100%);}

/* ============ Animaciones ============ */
@keyframes entrar{from{opacity:0;transform:translateY(12px) scale(.985);}to{opacity:1;transform:none;}}
.fila-usuario.nuevo .burbuja-usuario{transform-origin:100% 100%;animation:entrar .38s cubic-bezier(.2,.7,.2,1) both;}
[data-testid="stChatMessage"]:has(.marca-nuevo){animation:entrar .5s .1s cubic-bezier(.2,.7,.2,1) both;}
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] .marca-nuevo){display:none;}

/* ============ Tarjetas HTML ============ */
[class*="st-key-tarjeta_"]{position:relative;width:100%;gap:0;}
.tarjeta{display:flex;align-items:center;gap:.9rem;min-height:4.1rem;padding:.65rem .95rem .65rem .8rem;
  background:linear-gradient(180deg,#fff,#F8FBFF);border:1px solid var(--linea);border-radius:var(--r-md);
  box-shadow:0 1px 2px rgba(30,42,71,.05),0 6px 16px rgba(31,86,184,.08);
  transition:transform .15s,box-shadow .15s,border-color .15s,background .15s;}
.tarjeta-icono{position:relative;flex:none;display:grid;place-items:center;width:2.75rem;height:2.75rem;
  border-radius:13px;font-size:1.4rem;line-height:1;border:1px solid var(--linea);
  background:linear-gradient(135deg,var(--hielo),#DCEBFB);}
.tarjeta-num{position:absolute;top:-.5rem;left:-.5rem;display:grid;place-items:center;min-width:1.4rem;
  height:1.4rem;padding:0 .3rem;border-radius:999px;border:2px solid #fff;color:#fff;
  font-family:'Montserrat',sans-serif;font-weight:700;font-size:.74rem;line-height:1;
  background:linear-gradient(135deg,var(--azul-medio),var(--azul-fuerte));box-shadow:0 3px 8px rgba(31,86,184,.35);}
.tarjeta-titulo{flex:1;min-width:0;color:var(--navy);font-weight:600;font-size:1.03rem;line-height:1.3;}
.tarjeta-flecha{flex:none;font-size:1.6rem;line-height:1;color:var(--azul);opacity:.5;transition:transform .15s,opacity .15s;}
[class*="st-key-tarjeta_"]:hover .tarjeta{transform:translateY(-2px);border-color:var(--azul);
  box-shadow:var(--sombra-alta);background:linear-gradient(90deg,var(--hielo),#fff 80%);}
[class*="st-key-tarjeta_"]:hover .tarjeta-flecha{transform:translateX(3px);opacity:1;}
[class*="st-key-tarjeta_"]:active .tarjeta{transform:translateY(0);background:#DCEBFB;}
[class*="st-key-tarjeta_"]:has(button:focus-visible) .tarjeta{outline:3px solid rgba(47,123,217,.45);outline-offset:1px;}
[class*="st-key-tarjeta_"] [data-testid="stElementContainer"]:has(.stButton){position:absolute;inset:0;
  z-index:2;margin:0;width:100% !important;height:100% !important;}
[class*="st-key-tarjeta_"] .stButton,[class*="st-key-tarjeta_"] [data-testid="stButton"]{width:100% !important;height:100%;}
[class*="st-key-tarjeta_"] .stButton>button{width:100%;height:100%;min-height:0;opacity:0;cursor:pointer;}
[class*="st-key-tarjeta_"] [data-testid="stMarkdown"],
[class*="st-key-tarjeta_"] [data-testid="stMarkdownContainer"]{margin:0 !important;}
[data-testid="stHorizontalBlock"]:has([class*="st-key-tarjeta_"]){margin-bottom:-.25rem;}

/* ============ Elementos horizontales ============ */
.st-key-migas,.st-key-faq{flex-direction:row !important;flex-wrap:wrap;align-items:center;gap:.35rem !important;}
.st-key-migas{margin-top:.5rem;}
.st-key-migas>*,.st-key-faq>*{width:auto !important;flex:0 0 auto !important;}
.st-key-migas .stButton,.st-key-faq .stButton{width:auto !important;}
.st-key-migas [data-testid="stMarkdown"],.st-key-faq [data-testid="stMarkdown"]{margin:0 !important;}
.st-key-migas [data-testid="stElementContainer"]{display:flex;align-items:center;gap:.35rem;}
.st-key-migas [data-testid="stElementContainer"]:not(:last-child)::after{content:"›";color:var(--pizarra);font-size:1.2rem;line-height:1;}
.st-key-migas .stButton>button{width:auto;min-height:2.05rem;padding:.2rem .85rem;border-radius:999px;
  justify-content:center;border:1px solid var(--linea);background:#fff;color:var(--azul-fuerte);
  font-size:.92rem;font-weight:700;box-shadow:var(--sombra);}
.st-key-migas .stButton>button p{text-align:center;}
.st-key-migas .stButton>button:hover{background:var(--hielo);border-color:var(--azul);transform:translateY(-1px);}
.miga-actual{display:inline-block;padding:.32rem .95rem;border-radius:999px;color:#fff;font-weight:700;
  font-size:.92rem;line-height:1.3;background:linear-gradient(135deg,var(--azul-medio),var(--azul-fuerte));
  box-shadow:0 4px 10px rgba(31,86,184,.25);}
.st-key-faq .stButton>button{width:auto;}

/* Botón flotante alejado del input inferior */
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] #ies-opciones){height:0;overflow:hidden;margin:0 0 -1rem;}
#ies-opciones{scroll-margin-top:6.5rem;}
#ies-bajar{position:fixed;left:50%;bottom:7.5rem;z-index:1000;transform:translate(-50%,14px);opacity:0;
  pointer-events:none;border:0;border-radius:999px;padding:.55rem 1.15rem;cursor:pointer;color:#fff;
  font:600 .96rem 'Source Sans 3','Segoe UI',system-ui,sans-serif;
  background:linear-gradient(135deg,var(--azul-medio),var(--azul-fuerte));
  box-shadow:0 10px 24px rgba(31,86,184,.38);transition:opacity .2s,transform .2s,background .15s;}
#ies-bajar.visible{opacity:1;transform:translate(-50%,0);pointer-events:auto;}
#ies-bajar:hover{background:var(--navy);}
#ies-bajar:focus-visible{outline:3px solid rgba(47,123,217,.5);outline-offset:2px;}

/* ============ Barra lateral ============ */
[data-testid="stSidebar"]{border-right:1px solid rgba(213,226,243,.9);background-color:#F6FAFF;
  background-image:radial-gradient(420px 300px at 0% 0%,rgba(43,168,227,.20),transparent 65%),
  radial-gradient(380px 320px at 100% 100%,rgba(245,165,36,.12),transparent 65%),
  linear-gradient(180deg,#fff 0%,#EAF3FD 100%);box-shadow:6px 0 24px rgba(31,86,184,.06);}
[data-testid="stSidebar"] .stButton>button{justify-content:center;text-align:center;min-height:2.6rem;
  border-left-width:1px;border-left-color:var(--linea);}
[data-testid="stSidebar"] .stButton>button p{text-align:center;}
.lateral-cabecera{position:relative;overflow:hidden;text-align:center;background:var(--grad-marca);
  border-radius:var(--r-lg);padding:1.3rem 1rem 1.1rem;box-shadow:0 10px 24px rgba(31,86,184,.28);}
.lateral-cabecera::after{content:"";position:absolute;right:-40px;top:-50px;width:140px;height:140px;
  border-radius:50%;border:20px solid rgba(43,168,227,.30);pointer-events:none;}
.lateral-cabecera img{position:relative;z-index:1;width:88px;height:88px;border-radius:50%;background:#fff;
  padding:4px;box-shadow:0 0 0 4px rgba(255,255,255,.25);}
.lateral-nombre{position:relative;z-index:1;font-family:'Montserrat',sans-serif;font-weight:700;
  font-size:.95rem;line-height:1.3;color:#fff;margin:.8rem 0 0;}
.lateral-titulo{display:flex;align-items:center;gap:.5rem;color:var(--navy);font-family:'Montserrat',sans-serif;
  font-weight:700;font-size:.9rem;margin:1.2rem 0 .4rem;}
.lateral-titulo::before{content:"";width:4px;height:1.1em;border-radius:4px;background:var(--grad-aro);}
.ficha{display:flex;gap:.65rem;align-items:center;background:#fff;border:1px solid var(--linea);
  border-radius:var(--r-sm);padding:.5rem .7rem;margin:.4rem 0;font-size:.93rem;line-height:1.35;
  color:var(--navy);overflow-wrap:anywhere;box-shadow:var(--sombra);}
.ficha>span:first-child{flex:none;display:grid;place-items:center;width:2rem;height:2rem;border-radius:50%;
  background:#D6E9FB;color:var(--azul-fuerte);}
.ficha>span:first-child svg{width:1.05rem;height:1.05rem;fill:none;stroke:currentColor;stroke-width:2;
  stroke-linecap:round;stroke-linejoin:round;}
.ficha a{color:var(--azul-fuerte);font-weight:600;}
.lateral-uso{background:#fff;border:1px solid var(--ambar-linea);border-radius:var(--r-md);
  padding:.7rem .85rem;margin:.9rem 0 .5rem;box-shadow:var(--sombra);}
.lateral-uso .uso-fila{display:flex;justify-content:space-between;align-items:baseline;gap:.5rem;
  font-size:.9rem;font-weight:600;color:var(--navy);}
.lateral-uso .uso-fila b{font-family:'Montserrat',sans-serif;font-size:.95rem;color:var(--ambar-texto);}
.lateral-uso .uso-barra{height:7px;border-radius:99px;background:var(--ambar-suave);margin-top:.5rem;overflow:hidden;}
.lateral-uso .uso-barra i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--ambar),#F7C45E);}
.lateral-nota{display:flex;gap:.55rem;align-items:flex-start;font-size:.86rem;line-height:1.45;color:var(--pizarra);
  background:rgba(255,255,255,.7);border:1px dashed var(--linea);border-radius:var(--r-md);padding:.6rem .75rem;margin:.4rem 0;}

/* Botón de colapso: se funde con el fondo y queda alineado con el margen de la tarjeta */
[data-testid="stSidebarHeader"]{background:transparent;height:auto;min-height:0;padding:.7rem 1.5rem .1rem;
  margin-bottom:0;justify-content:flex-end;}
[data-testid="stSidebarCollapseButton"] button,[data-testid="stSidebarCollapseButton"]{color:var(--pizarra);}
[data-testid="stSidebarCollapseButton"] button{background:transparent;border:0;box-shadow:none;border-radius:8px;opacity:.7;}
[data-testid="stSidebarCollapseButton"] button:hover{background:rgba(47,123,217,.12);color:var(--azul-fuerte);opacity:1;}
[data-testid="stSidebarCollapseButton"] svg{color:inherit;}

/* Botón para reabrir la barra lateral: vive dentro del toolbar oculto, así que se fuerza visible */
[data-testid="stExpandSidebarButton"],[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] *,[data-testid="stExpandSidebarButton"] *{visibility:visible !important;}
[data-testid="stExpandSidebarButton"],[data-testid="stSidebarCollapsedControl"] button{
  color:var(--azul-fuerte);background:#fff;border:1px solid var(--linea);border-radius:10px;
  box-shadow:var(--sombra);z-index:100;}
[data-testid="stExpandSidebarButton"]:hover,[data-testid="stSidebarCollapsedControl"] button:hover{
  background:var(--hielo);border-color:var(--azul);}

/* ============ Caja de texto ============ */
[data-testid="stChatInput"]{background:#fff;border:1.5px solid #C3D4EC;border-radius:var(--r-lg);
  box-shadow:0 2px 4px rgba(30,42,71,.08),0 12px 30px rgba(31,86,184,.22);}
[data-testid="stChatInput"]:focus-within{border-color:var(--azul);box-shadow:0 0 0 4px rgba(47,123,217,.20);}
[data-testid="stChatInput"] textarea{color:var(--navy);}
[data-testid="stChatInput"] textarea::placeholder{color:#6C7A9C !important;-webkit-text-fill-color:#6C7A9C;opacity:1 !important;}
[data-testid="stChatInputSubmitButton"]:not(:disabled){background:var(--azul-fuerte);color:#fff;
  border-radius:50%;transition:background .15s,transform .15s;}
[data-testid="stChatInputSubmitButton"]:not(:disabled):hover{background:var(--navy);transform:scale(1.06);}

/* ============ Pantallas chicas ============ */
@media (max-width:640px){
  .block-container{margin:0 auto;padding:3.2rem .8rem 4rem;border-radius:0;border-width:0;
    background:transparent;box-shadow:none;-webkit-backdrop-filter:none;backdrop-filter:none;}
  div.hero{flex-direction:column;text-align:center;padding:1.4rem 1.2rem;gap:1rem;}
  div.hero .hero-marco{width:80px;height:80px;}
  div.hero .hero-pistas{display:none;}
  div.stMarkdown div.hero h1{font-size:1.4rem;}
  .burbuja-usuario{max-width:90%;}
  [data-testid="stChatMessage"]{padding:.85rem .95rem;}
  div.barra .barra-ia{display:none;}
  [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] .barra){top:3.2rem;}
  header[data-testid="stHeader"]{background:linear-gradient(to bottom,rgba(234,242,253,.96) 60%,rgba(234,242,253,0));}
  .fila-usuario,#ies-opciones{scroll-margin-top:7.5rem;}
  [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] .barra)::before{left:-.8rem;right:-.8rem;bottom:-4rem;
    background:linear-gradient(to bottom,var(--fondo-base) 40%,rgba(237,243,252,0) 100%);}}
@media (prefers-reduced-motion:reduce){*{transition:none !important;animation:none !important;}}
</style>"""