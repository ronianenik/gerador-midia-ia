import io
import json
import os
import re
import tempfile
import urllib.parse
from gtts import gTTS
import google.generativeai as genai
import requests
import streamlit as st

# Tenta importar MoviePy com fallback
try:
    from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips

    MOVIEPY_DISPONIVEL = True
except Exception:
    MOVIEPY_DISPONIVEL = False

st.set_page_config(
    page_title="Central de Conteúdo IA",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📱 Gerador Multi-Formato de Conteúdo com IA")
st.markdown(
    "Crie Posts Fixos, Carrosséis ou Vídeos curtos com mídias e áudio sincronizado."
)

# Chaves vindas do Streamlit Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
pexels_key = st.secrets.get("PEXELS_API_KEY", "")

with st.sidebar:
    st.header("⚙️ Status das APIs")
    if gemini_key:
        st.success("⚡ Gemini API: Conectado")
    else:
        st.error("❌ GEMINI_API_KEY ausente nos Secrets")

    if pexels_key:
        st.success("⚡ Pexels API: Conectado")
    else:
        st.warning("⚠️ PEXELS_API_KEY ausente (Vídeos indisponíveis)")

# Formulário
with st.form("form_conteudo"):
    tipo_formato = st.radio(
        "Escolha o formato do conteúdo:",
        ["Post Fixo", "Carrossel", "Vídeo (Reels/TikTok)"],
        horizontal=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        tema = st.text_input(
            "Tema do conteúdo:",
            placeholder="Ex: 3 exercícios de musculação para corredores",
        )
        tom = st.selectbox(
            "Tom de voz:",
            [
                "Educacional & Técnico",
                "Descontraído & Dinâmico",
                "Motivacional & Inspirador",
                "Vendedor & Persuasivo",
            ],
        )
    with col2:
        publico = st.text_input(
            "Público-alvo:", placeholder="Ex: Atletas corredores"
        )
        num_slides = st.slider("Quantidade de slides/cenas:", 3, 7, 4)

    btn_gerar = st.form_submit_button("🚀 Gerar Conteúdo Completo")


# --- FUNÇÕES TRATADAS ---


def sanitizar_prompt(texto):
    """Limpa quebras de linha e caracteres especiais para evitar erros em URLs."""
    if not texto:
        return "sports workout"
    texto_limpo = str(texto).replace("\n", " ").replace("\r", " ").replace('"', "").replace("'", "")
    texto_limpo = re.sub(r"\s+", " ", texto_limpo).strip()
    return texto_limpo[:150]


def gerar_url_imagem(prompt, aspecto="1080x1080"):
    w, h = aspecto.split("x")
    prompt_limpo = sanitizar_prompt(prompt)
    prompt_encoded = urllib.parse.quote(f"{prompt_limpo}, high quality, photography")
    return f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={w}&height={h}&nologo=true"


def baixar_bytes_midia(url):
    """Baixa arquivos com timeout e tratamento de erro."""
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
        return None
    query_limpa = sanitizar_prompt(query)
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query_limpa)}&per_page=1&orientation=portrait"
    headers = {"Authorization": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("videos"):
                video_files = data["videos"][0].get("video_files", [])
                for v in video_files:
                    if v.get("file_type") == "video/mp4":
                        return v.get("link")
    except Exception:
        pass
    return None


def renderizar_video_completo(cenas, pexels_key):
    """Processa o vídeo compilado via MoviePy se as dependências existirem."""
    if not MOVIEPY_DISPONIVEL:
        return None

    clips = []
    arquivos_temp = []

    try:
        for cena in cenas:
            narracao = cena.get("narracao", "")
            busca = cena.get("busca_pexels", "exercise")

            # Áudio
            tts = gTTS(text=narracao, lang="pt", tld="com.br")
            f_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(f_audio.name)
            f_audio.close()
            arquivos_temp.append(f_audio.name)
            audio_clip = AudioFileClip(f_audio.name)

            # Vídeo
            url_vid = buscar_video_pexels(busca, pexels_key)
            if not url_vid:
                url_vid = buscar_video_pexels("fitness", pexels_key)

            if url_vid:
                vid_content = baixar_bytes_midia(url_vid)
                if vid_content:
                    f_vid = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".mp4"
                    )
                    f_vid.write(vid_content)
                    f_vid.close()
                    arquivos_temp.append(f_vid.name)

                    video_clip = VideoFileClip(f_vid.name)
                    duracao_audio = audio_clip.duration

                    if video_clip.duration < duracao_audio:
                        video_clip = video_clip.loop(duration=duracao_audio)
                    else:
                        video_clip = video_clip.subclip(0, duracao_audio)

                    video_clip = video_clip.set_audio(audio_clip)
                    clips.append(video_clip)

        if clips:
            video_final = concatenate_videoclips(clips, method="compose")
            f_output = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp4"
            )
            f_output.close()
            arquivos_temp.append(f_output.name)

            video_final.write_videofile(
                f_output.name,
                codec="libx264",
                audio_codec="aac",
                fps=24,
                preset="ultrafast",
                logger=None,
            )

            with open(f_output.name, "rb") as f:
                video_bytes = f.read()

            return video_bytes

    except Exception:
        return None

    finally:
        for f_path in arquivos_temp:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception:
                    pass
    return None


# --- EXECUÇÃO ---

if btn_gerar:
    if not gemini_key:
        st.error("Configure a chave GEMINI_API_KEY nos Secrets do Streamlit.")
    elif not tema:
        st.warning("Preencha o tema do conteúdo.")
    else:
        with st.spinner("🤖 A IA está criando o conteúdo..."):
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-3.6-flash")

                if tipo_formato == "Post Fixo":
                    prompt_sistema = f"""
                    Crie um Post Fixo sobre: {tema}. Público: {publico}. Tom: {tom}.
                    Responda ESTRITAMENTE em JSON sem quebras de linha nos valores:
                    {{
                        "titulo_imagem": "Texto de impacto para a arte",
                        "prompt_imagem": "Prompt curto em ingles descrevendo a imagem fotográfica sem aspas",
                        "legenda": "Legenda completa com hashtags"
                    }}
                    """

                elif tipo_formato == "Carrossel":
                    prompt_sistema = f"""
                    Crie um Carrossel de {num_slides} slides sobre: {tema}. Público: {publico}. Tom: {tom}.
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
                    Crie um roteiro em {num_slides} cenas curtas sobre: {tema}. Público: {publico}. Tom: {tom}.
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

                st.success("✨ Conteúdo gerado com sucesso!")

                # --- EXIBIÇÃO: POST FIXO ---
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

                # --- EXIBIÇÃO: CARROSSEL ---
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

                # --- EXIBIÇÃO: VÍDEO ---
                else:
                    cenas = dados.get("cenas", [])
                    c1, c2 = st.columns(2)

                    with c1:
                        st.subheader("🎬 Vídeo Editado")
                        video_bytes = None

                        if pexels_key:
                            with st.spinner(
                                "🎥 Compilando vídeo e áudio..."
                            ):
                                video_bytes = renderizar_video_completo(
                                    cenas, pexels_key
                                )

                        if video_bytes:
                            st.video(video_bytes)
                            st.download_button(
                                "📥 Baixar Vídeo MP4",
                                video_bytes,
                                "video_final.mp4",
                                "video/mp4",
                            )
                        else:
                            st.info(
                                "ℹ️ Exibindo pré-visualização individual das cenas:"
                            )
                            for cena in cenas:
                                url_v = buscar_video_pexels(
                                    cena.get("busca_pexels"), pexels_key
                                )
                                if url_v:
                                    st.video(url_v)

                    with c2:
                        st.subheader("🗣️ Roteiro e Narração por Cena")
                        for cena in cenas:
                            st.write(
                                f"**Cena {cena.get('numero')}:** {cena.get('narracao')}"
                            )

                            # Gerar áudio individual para ouvir
                            tts = gTTS(
                                text=cena.get("narracao"),
                                lang="pt",
                                tld="com.br",
                            )
                            fp = io.BytesIO()
                            tts.write_to_fp(fp)
                            fp.seek(0)
                            st.audio(fp, format="audio/mp3")
                            st.caption(
                                f"Busca Pexels: `{cena.get('busca_pexels')}`"
                            )
                            st.divider()

                        st.subheader("📝 Legenda do Vídeo")
                        st.text_area(
                            "Copie o texto:", dados.get("legenda"), height=200
                        )

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")