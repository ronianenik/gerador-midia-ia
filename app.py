import io
import json
import re
import urllib.parse
from gtts import gTTS
import google.generativeai as genai
import requests
import streamlit as st

st.set_page_config(
    page_title="Central de Conteúdo IA",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- GERENCIAMENTO DE ESTADO / PROJETOS ---
if "projetos" not in st.session_state:
    st.session_state.projetos = ["Geral", "RS Fisioterapia e Quiropraxia"]

# Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
pexels_key = st.secrets.get("PEXELS_API_KEY", "")

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("📁 Projetos")

    # Criar novo projeto
    with st.expander("➕ Criar Novo Projeto", expanded=False):
        novo_proj = st.text_input(
            "Nome do Projeto:", placeholder="Ex: Projeto Tráfego"
        )
        if st.button("Salvar Projeto"):
            if novo_proj and novo_proj.strip() not in st.session_state.projetos:
                st.session_state.projetos.append(novo_proj.strip())
                st.success(f"Projeto '{novo_proj.strip()}' adicionado!")
                st.rerun()

    # Seleção do Projeto Ativo
    projeto_ativo = st.selectbox(
        "Selecione o projeto ativo:", st.session_state.projetos
    )

    st.divider()
    st.header("⚙️ Status das APIs")
    if gemini_key:
        st.success("⚡ Gemini API: Conectado")
    else:
        st.error("❌ GEMINI_API_KEY ausente nos Secrets")

    if pexels_key:
        st.success("⚡ Pexels API: Conectado")
    else:
        st.warning("⚠️ PEXELS_API_KEY ausente (Vídeos indisponíveis)")

# --- CABEÇALHO ---
st.title("📱 Gerador Multi-Formato de Conteúdo")
st.caption(f"📌 Projeto Ativo: **{projeto_ativo}**")

# Seleção do formato fora do formulário para atualizar os campos em tempo real
tipo_formato = st.radio(
    "Escolha o formato do conteúdo:",
    ["Post Fixo", "Carrossel", "Vídeo (Reels/TikTok)"],
    horizontal=True,
)

# --- FORMULÁRIO COM CAMPOS DINÂMICOS ---
with st.form("form_conteudo"):

    # 1. Post Fixo: Apenas Tema e Público-alvo
    if tipo_formato == "Post Fixo":
        col1, col2 = st.columns(2)
        with col1:
            tema = st.text_input(
                "Tema do conteúdo:", placeholder="Ex: Benefícios da quiropraxia"
            )
        with col2:
            publico = st.text_input(
                "Público-alvo:", placeholder="Ex: Pessoas com dores nas costas"
            )
        tom = "Educacional & Persuasivo"
        num_slides = 1

    # 2. Carrossel: Tema, Público-alvo e Quantidade de Slides
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
        tom = "Educacional & Técnico"

    # 3. Vídeo: Tema, Público-alvo e Tom de Voz
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
        num_slides = 3  # Padrão de 3 cenas curtas para reels/tiktok

    btn_gerar = st.form_submit_button("🚀 Gerar Conteúdo Completo")


# --- FUNÇÕES AUXILIARES ---


def sanitizar_prompt(texto):
    if not texto:
        return "sports workout"
    texto_limpo = (
        str(texto)
        .replace("\n", " ")
        .replace("\r", " ")
        .replace('"', "")
        .replace("'", "")
    )
    return re.sub(r"\s+", " ", texto_limpo).strip()[:150]


def gerar_url_imagem(prompt, aspecto="1080x1080"):
    w, h = aspecto.split("x")
    prompt_limpo = sanitizar_prompt(prompt)
    prompt_encoded = urllib.parse.quote(f"{prompt_limpo}, high quality, photography")
    return f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={w}&height={h}&nologo=true"


def baixar_bytes_midia(url):
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
        )
        if resp.status_code == 200:
            return resp.content
    except Exception:
        pass
    return None


def buscar_video_pexels(query, api_key):
    if not api_key:
        return None, None
    query_limpa = sanitizar_prompt(query)
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


# --- GERAÇÃO E EXIBIÇÃO ---

if btn_gerar:
    if not gemini_key:
        st.error("Configure a chave GEMINI_API_KEY nos Secrets do Streamlit.")
    elif not tema:
        st.warning("Preencha o tema do conteúdo.")
    else:
        with st.spinner("🤖 A IA está criando o conteúdo..."):
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-2.5-flash")

                if tipo_formato == "Post Fixo":
                    prompt_sistema = f"""
                    Crie um Post Fixo para o projeto '{projeto_ativo}'.
                    Tema: {tema}. Público: {publico}. Tom: {tom}.
                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "titulo_imagem": "Texto de impacto para a arte",
                        "prompt_imagem": "Prompt curto em ingles descrevendo a imagem fotográfica sem aspas",
                        "legenda": "Legenda completa com hashtags"
                    }}
                    """

                elif tipo_formato == "Carrossel":
                    prompt_sistema = f"""
                    Crie um Carrossel de {num_slides} slides para o projeto '{projeto_ativo}'.
                    Tema: {tema}. Público: {publico}. Tom: {tom}.
                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "slides": [
                            {{
                                "numero": 1,
                                "texto_slide": "Resumo do slide",
                                "prompt_imagem": "Prompt curto em ingles para a imagem do slide sem aspas"
                            }}
                        ],
                        "legenda": "Legenda do post"
                    }}
                    """

                else:  # Vídeo
                    prompt_sistema = f"""
                    Crie um roteiro em {num_slides} cenas curtas para o projeto '{projeto_ativo}'.
                    Tema: {tema}. Público: {publico}. Tom: {tom}.
                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "cenas": [
                            {{
                                "numero": 1,
                                "narracao": "Texto curto falado na cena",
                                "busca_pexels": "duas palavras em ingles para busca de video"
                            }}
                        ],
                        "legenda": "Legenda do post"
                    }}
                    """

                response = model.generate_content(
                    prompt_sistema,
                    generation_config={
                        "response_mime_type": "application/json"
                    },
                )
                dados = json.loads(response.text)

                st.success(f"✨ Conteúdo para '{projeto_ativo}' gerado com sucesso!")

                # --- RESULTADO: POST FIXO ---
                if tipo_formato == "Post Fixo":
                    c1, c2 = st.columns(2)
                    with c1:
                        url_img = gerar_url_imagem(
                            dados.get("prompt_imagem", tema)
                        )
                        st.image(url_img, use_container_width=True)
                        st.info(
                            f"💡 **Texto na Imagem:** {dados.get('titulo_imagem')}"
                        )

                        img_bytes = baixar_bytes_midia(url_img)
                        if img_bytes:
                            st.download_button(
                                "📥 Baixar Imagem",
                                img_bytes,
                                "post_fixo.jpg",
                                "image/jpeg",
                            )
                    with c2:
                        st.subheader("📝 Legenda")
                        st.text_area(
                            "Copie o texto:", dados.get("legenda"), height=300
                        )

                # --- RESULTADO: CARROSSEL ---
                elif tipo_formato == "Carrossel":
                    slides = dados.get("slides", [])
                    cols = st.columns(min(len(slides), 5))

                    for idx, slide in enumerate(slides):
                        col_target = cols[idx % 5]
                        with col_target:
                            st.markdown(f"**Slide {slide.get('numero')}**")
                            url_img = gerar_url_imagem(
                                slide.get("prompt_imagem", tema)
                            )
                            st.image(url_img, use_container_width=True)
                            st.caption(slide.get("texto_slide"))

                            img_bytes = baixar_bytes_midia(url_img)
                            if img_bytes:
                                st.download_button(
                                    f"📥 Slide {slide.get('numero')}",
                                    img_bytes,
                                    f"slide_{slide.get('numero')}.jpg",
                                    "image/jpeg",
                                )

                    st.divider()
                    st.subheader("📝 Legenda")
                    st.text_area(
                        "Copie o texto:", dados.get("legenda"), height=250
                    )

                # --- RESULTADO: VÍDEO (COM DOWNLOADS INDIVIDUAIS) ---
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

                            # 1. Áudio Narração + Botão Download Áudio
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

                            # 2. Vídeo Pexels + Botão Download Vídeo
                            if pexels_key:
                                url_v, vid_bytes = buscar_video_pexels(
                                    busca_c, pexels_key
                                )
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
                    st.text_area(
                        "Copie o texto:", dados.get("legenda"), height=200
                    )

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
