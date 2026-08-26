import io
import json
import re
import urllib.parse
from gtts import gTTS
import google.generativeai as genai
import requests
import streamlit as st

st.set_page_config(
    page_title="Central de Conteúdo IA - Gemini 3.6 Flash",
    page_icon="📱",
    layout="wide",
)

# --- CONFIGURAÇÃO DE SECRETS ---
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
pexels_key = st.secrets.get("PEXELS_API_KEY", "")

# --- CABEÇALHO ---
<<<<<<< HEAD
st.title("📱 Gerador Multi-Formato de Conteúdo")

# Status simples das APIs no topo
#col_st1, col_st2 = st.columns(2)
#with col_st1:
#    if gemini_key:
#        st.success("⚡ Gemini 3.6 Flash API: Conectado", icon="✅")
#    else:
#        st.error("❌ GEMINI_API_KEY ausente nos Secrets")
#with col_st2:
#    if pexels_key:
#        st.success("⚡ Pexels API (Fotos Reais & Vídeos): Conectado", icon="✅")
#    else:
#        st.warning("⚠️ PEXELS_API_KEY ausente (Usando IA para imagens)")
=======
st.title("📱 Gerador de Conteúdo")
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50

st.divider()
 
tipo_formato = st.radio(
    "Escolha o formato do conteúdo:",
    ["Post Fixo", "Carrossel", "Vídeo (Reels/TikTok)"],
    horizontal=True,
)

with st.form("form_conteudo"):

    if tipo_formato == "Post Fixo":
        col1, col2 = st.columns(2)
        with col1:
            tema = st.text_input(
                "Tema do conteúdo:", placeholder="Ex: Exercícios essenciais para corredores"
            )
        with col2:
            publico = st.text_input(
                "Público-alvo:", placeholder="Ex: Atletas corredores"
            )
        
        estilo_imagem = st.text_input(
            "🎨 Estilo / Detalhes da Imagem (opcional):",
            placeholder="Ex: Homem com seus 40 anos correndo na rua de dia, estilo anime",
        )
        tom = "Educacional & Persuasivo"
        num_slides = 1

    elif tipo_formato == "Carrossel":
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            tema = st.text_input(
                "Tema do conteúdo:", placeholder="Ex: 5 Alongamentos pós-corrida"
            )
        with col2:
            publico = st.text_input(
                "Público-alvo:", placeholder="Ex: Corredores de rua"
            )
        with col3:
            num_slides = st.slider("Quantidade de slides:", 3, 7, 5)

        estilo_imagem = st.text_input(
            "🎨 Estilo / Detalhes das Imagens (opcional):",
            placeholder="Ex: Fotografia realista, iluminação dramática, tom azulado",
        )
        tom = "Educacional & Técnico"

    else:
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            tema = st.text_input(
                "Tema do conteúdo:",
                placeholder="Ex: 3 exercícios essenciais para corredores",
            )
        with col2:
            publico = st.text_input(
                "Público-alvo:", placeholder="Ex: Atletas corredores"
            )
        with col3:
            tom = st.selectbox(
                "Tom de voz:",
                [
                    "Educacional & Técnico",
                    "Descontraído & Dinâmico",
                    "Motivacional & Inspirador",
                    "Vendedor & Persuasivo",
                ],
            )

        estilo_imagem = st.text_input(
            "🎨 Estilo / Detalhes dos Vídeos (opcional):",
            placeholder="Ex: Vídeos dinâmicos em ambiente urbano, iluminação natural",
        )
        num_slides = 3

    btn_gerar = st.form_submit_button("🚀 Gerar Conteúdo Completo")

<<<<<<< HEAD
=======

# --- FUNÇÕES AUXILIARES & SANITIZAÇÃO DE IMAGENS ---

>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
def sanitizar_prompt(texto):
    if not texto:
        return "fitness athletic"
    texto_limpo = (
        str(texto)
        .replace("\n", " ")
        .replace("\r", " ")
        .replace('"', "")
        .replace("'", "")
    )
    return re.sub(r"\s+", " ", texto_limpo).strip()[:200]


MAPA_TERMOS_PROBLEMATICOS = {
    "bulgarian": "split squat gym workout",
    "calf": "leg ankle exercise gym",
    "calves": "leg workout gym athlete",
    "turkey": "gym workout athlete",
}

def sanitizar_busca_fitness(query):
    """Evita falsos positivos como fotos de bezerros (calf) ou países (Bulgaria)."""
    query_limpa = sanitizar_prompt(query).lower()
    
    palavras = query_limpa.split()
    novas_palavras = []
    for p in palavras:
        if p in MAPA_TERMOS_PROBLEMATICOS:
            novas_palavras.append(MAPA_TERMOS_PROBLEMATICOS[p])
        else:
            novas_palavras.append(p)
    query_limpa = " ".join(novas_palavras)
    return query_limpa


MAPA_TERMOS_PROBLEMATICOS = {
    "bulgarian": "split squat gym workout",
    "calf": "leg ankle exercise gym",
    "calves": "leg workout gym athlete",
    "turkey": "gym workout athlete",
}

def sanitizar_busca_fitness(query):
    query_limpa = sanitizar_prompt(query).lower()

    palavras = query_limpa.split()
    novas_palavras = []
    for p in palavras:
        if p in MAPA_TERMOS_PROBLEMATICOS:
            novas_palavras.append(MAPA_TERMOS_PROBLEMATICOS[p])
        else:
            novas_palavras.append(p)
    query_limpa = " ".join(novas_palavras)
            
    palavras_chave_fitness = ["gym", "workout", "fitness", "athlete", "exercise", "sport", "running", "runner"]
    if not any(word in query_limpa for word in palavras_chave_fitness):
        query_limpa += " gym workout"
        
    return query_limpa


def baixar_bytes_midia(url):
    try:
        resp = requests.get(
            url,
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


def obter_imagem_post(query_ingles, api_key, urls_usadas=None):
<<<<<<< HEAD
=======
    """Busca foto no Pexels ou gera via IA conforme estilo solicitado."""
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
    if urls_usadas is None:
        urls_usadas = set()

    query_limpa = sanitizar_busca_fitness(query_ingles)
    
<<<<<<< HEAD
    # 1. Tenta buscar Foto Real no Pexels
    if api_key:
=======
    # Se o prompt exige um estilo artístico (ex: anime, cartoon, 3d, illustration), prioriza IA
    estilos_artisticos = ["anime", "manga", "illustration", "drawing", "3d render", "cartoon", "art style"]
    quer_estilo_artistico = any(estilo in query_limpa for estilo in estilos_artisticos)

    # 1. Tenta buscar no Pexels se for foto realista
    if api_key and not quer_estilo_artistico:
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
        url_pexels = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query_limpa)}&per_page=5&orientation=square"
        headers = {"Authorization": api_key}
        try:
            resp = requests.get(url_pexels, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                photos = data.get("photos", [])
                for photo in photos:
                    src_img = photo["src"].get("large2x") or photo["src"].get("medium")
                    if src_img and src_img not in urls_usadas:
                        urls_usadas.add(src_img)
                        img_bytes = baixar_bytes_midia(src_img)
                        return src_img, img_bytes
<<<<<<< HEAD
                # Se todas já foram usadas, pega a primeira disponível
                if photos:
                    src_img = photos[0]["src"].get("large2x") or photos[0]["src"].get("medium")
                    img_bytes = baixar_bytes_midia(src_img)
                    return src_img, img_bytes
        except Exception:
            pass

    # 2. Fallback caso Pexels não retorne
    prompt_encoded = urllib.parse.quote(f"{query_limpa}, professional photographic portrait, sharp focus")
=======
        except Exception:
            pass

    # 2. Gerador IA (Ideal para estilos artísticos como Anime ou quando o Pexels não encontra)
    prompt_encoded = urllib.parse.quote(f"{query_limpa}, high quality, detailed")
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
    url_ia = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1080&height=1080&nologo=true&model=flux"
    return url_ia, baixar_bytes_midia(url_ia)


def buscar_video_pexels(query, api_key):
    if not api_key:
        return None, None
    query_limpa = sanitizar_busca_fitness(query)
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query_limpa)}&per_page=1&orientation=portrait"
    headers = {"Authorization": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("videos"):
                video_files = data["videos"][0].get("video_files", [])
                if video_files:
                    link_vid = video_files[0].get("link")
                    vid_bytes = baixar_bytes_midia(link_vid)
                    return link_vid, vid_bytes
    except Exception:
        pass
    return None, None

if btn_gerar:
    if not gemini_key:
        st.error("Configure a chave GEMINI_API_KEY nos Secrets do Streamlit.")
    elif not tema:
        st.warning("Preencha o tema do conteúdo.")
    else:
<<<<<<< HEAD
        with st.spinner("🤖 O Gemini 3.6 Flash está criando o conteúdo e selecionando as imagens..."):
=======
        with st.spinner("🤖 O Gemini 3.6 Flash está criando o conteúdo e personalizando as imagens..."):
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-3.6-flash")

                detalhe_visual_prompt = f"Estilo/Detalhe Visual Exigido pelo Usuário: {estilo_imagem}" if estilo_imagem else "Estilo: Fotografia realista de alta qualidade"

                if tipo_formato == "Post Fixo":
                    prompt_sistema = f"""
                    Crie um Post Fixo.
                    Tema: {tema}. Público: {publico}. Tom: {tom}.
<<<<<<< HEAD

                    REGRAS PARA "busca_imagem":
                    - Use 3 a 4 palavras em INGLÊS focadas em fitness/academia.
                    - NUNCA use palavras ambíguas como 'Bulgarian' (use 'split squat gym') ou 'calf' (use 'leg exercise gym').
                    - SEMPRE inclua o contexto como 'gym', 'fitness', 'athlete' ou 'workout'.
=======
                    {detalhe_visual_prompt}

                    REGRAS PARA "busca_imagem":
                    - Crie um prompt completo em INGLÊS incorporando a cena e o estilo visual solicitado pelo usuário.
                    - Se o usuário pediu estilo (ex: anime, 3d, foto realista), inclua explicitamente no prompt em inglês.
                    - Evite palavras ambíguas (ex: use 'split squat' em vez de 'bulgarian').
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50

                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "titulo_imagem": "Texto de impacto para a arte",
<<<<<<< HEAD
                        "busca_imagem": "3 a 4 palavras em ingles com contexto de academia/fitness",
=======
                        "busca_imagem": "Prompt detalhado em ingles descrevendo a cena e o estilo visual",
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
                        "legenda": "Legenda completa com hashtags"
                    }}
                    """

                elif tipo_formato == "Carrossel":
                    prompt_sistema = f"""
                    Crie um Carrossel de {num_slides} slides.
                    Tema: {tema}. Público: {publico}. Tom: {tom}.
<<<<<<< HEAD

                    REGRAS OBRIGATÓRIAS PARA "busca_imagem":
                    - Cada slide DEVE ter um termo de busca DIFERENTE e específico em INGLÊS.
                    - NUNCA use palavras ambíguas como 'Bulgarian' (use 'split squat gym') ou 'calf' (use 'leg workout gym').
                    - SEMPRE inclua termos de contexto como 'gym', 'fitness', 'athlete' ou 'workout'.
                    - Exemplo agachamento búlgaro: 'split squat gym workout'
                    - Exemplo stiff: 'deadlift exercise gym athlete'
                    - Exemplo panturrilha: 'leg ankle exercise gym'
=======
                    {detalhe_visual_prompt}

                    REGRAS PARA "busca_imagem":
                    - Cada slide DEVE ter um prompt em INGLÊS específico para a cena daquele slide.
                    - Mantenha a consistência do estilo visual solicitado pelo usuário em TODOS os slides.
                    - Se o usuário pediu estilo anime, todos os prompts devem especificar 'anime style'.
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50

                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "slides": [
                            {{
                                "numero": 1,
                                "texto_slide": "Resumo do slide",
<<<<<<< HEAD
                                "busca_imagem": "3 a 4 palavras em ingles especificas para o exercicio/tema do slide"
=======
                                "busca_imagem": "Prompt em ingles com cena e estilo para o slide"
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
                            }}
                        ],
                        "legenda": "Legenda do post"
                    }}
                    """

                else:  # Vídeo
                    prompt_sistema = f"""
                    Crie um roteiro em {num_slides} cenas curtas.
                    Tema: {tema}. Público: {publico}. Tom: {tom}.
<<<<<<< HEAD

                    REGRAS PARA "busca_pexels":
                    - Use 2 a 3 palavras em INGLÊS específicas para a cena.
                    - SEMPRE inclua contexto como 'gym', 'workout', 'runner' ou 'fitness'.
=======
                    {detalhe_visual_prompt}
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50

                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "cenas": [
                            {{
                                "numero": 1,
                                "narracao": "Texto curto falado na cena",
<<<<<<< HEAD
                                "busca_pexels": "duas ou tres palavras em ingles para busca de video"
=======
                                "busca_pexels": "2 a 3 palavras em ingles para buscar o video"
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50
                            }}
                        ],
                        "legenda": "Legenda do post"
                    }}
                    """

                response = model.generate_content(
                    prompt_sistema,
                    generation_config={"response_mime_type": "application/json"},
                )
                dados = json.loads(response.text)

<<<<<<< HEAD
                st.success("✨ Conteúdo gerado com sucesso pelo Gemini 3.6 Flash!")
=======
                st.success("✨ Conteúdo e imagens gerados com sucesso!")
>>>>>>> 01e93022106523742a0473a0791f3f55a68cee50

                if tipo_formato == "Post Fixo":
                    c1, c2 = st.columns(2)
                    with c1:
                        busca_img = dados.get("busca_imagem", tema)
                        url_img, img_bytes = obter_imagem_post(busca_img, pexels_key)
                        
                        st.image(url_img, use_container_width=True)
                        st.info(f"💡 **Texto na Imagem:** {dados.get('titulo_imagem')}")
                        st.caption(f"🔍 Prompt da Imagem: `{busca_img}`")

                        if img_bytes:
                            st.download_button(
                                "📥 Baixar Imagem HD",
                                img_bytes,
                                "post_fixo.jpg",
                                "image/jpeg",
                            )
                    with c2:
                        st.subheader("📝 Legenda")
                        st.text_area("Copie o texto:", dados.get("legenda"), height=300)

                elif tipo_formato == "Carrossel":
                    slides = dados.get("slides", [])
                    cols = st.columns(min(len(slides), 5))
                    urls_usadas = set()

                    for idx, slide in enumerate(slides):
                        col_target = cols[idx % 5]
                        with col_target:
                            st.markdown(f"**Slide {slide.get('numero')}**")
                            busca_img = slide.get("busca_imagem", tema)
                            url_img, img_bytes = obter_imagem_post(busca_img, pexels_key, urls_usadas)
                            
                            st.image(url_img, use_container_width=True)
                            st.caption(slide.get("texto_slide"))

                            if img_bytes:
                                st.download_button(
                                    f"📥 Slide {slide.get('numero')}",
                                    img_bytes,
                                    f"slide_{slide.get('numero')}.jpg",
                                    "image/jpeg",
                                    key=f"dl_slide_{idx}",
                                )

                    st.divider()
                    st.subheader("📝 Legenda")
                    st.text_area("Copie o texto:", dados.get("legenda"), height=250)

                else:
                    cenas = dados.get("cenas", [])
                    st.subheader("🎬 Cenas do Vídeo & Mídias para Download")

                    cols_cenas = st.columns(len(cenas))
                    for idx, cena in enumerate(cenas):
                        col_target = cols_cenas[idx]
                        num_c = cena.get("numero")
                        narracao_c = cena.get("narracao")
                        busca_c = cena.get("busca_pexels")

                        with col_target:
                            st.markdown(f"### Cena {num_c}")
                            st.write(f"🗣️ **Locução:** {narracao_c}")

                            tts = gTTS(text=narracao_c, lang="pt", tld="com.br")
                            fp = io.BytesIO()
                            tts.write_to_fp(fp)
                            audio_bytes = fp.getvalue()

                            st.audio(audio_bytes, format="audio/mp3")
                            st.download_button(
                                f"📥 Baixar Áudio C{num_c}",
                                audio_bytes,
                                file_name=f"audio_cena_{num_c}.mp3",
                                mime="audio/mp3",
                                key=f"dl_audio_{num_c}",
                            )

                            if pexels_key:
                                url_v, vid_bytes = buscar_video_pexels(busca_c, pexels_key)
                                if url_v:
                                    st.video(url_v)
                                    if vid_bytes:
                                        st.download_button(
                                            f"📥 Baixar Vídeo C{num_c}",
                                            vid_bytes,
                                            file_name=f"video_cena_{num_c}.mp4",
                                            mime="video/mp4",
                                            key=f"dl_vid_{num_c}",
                                        )
                                else:
                                    st.caption("🎥 Vídeo não encontrado.")

                            st.caption(f"🔍 Busca Pexels: `{busca_c}`")

                    st.divider()
                    st.subheader("📝 Legenda do Vídeo")
                    st.text_area("Copie o texto:", dados.get("legenda"), height=200)

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
