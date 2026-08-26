import io
import json
import os
import re
import tempfile
import urllib.parse
from gtts import gTTS
import google.generativeai as genai
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips
import requests
import streamlit as st

# Configuração da página Web
st.set_page_config(
    page_title="Central de Conteúdo IA",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📱 Gerador Multi-Formato de Conteúdo com IA")
st.markdown(
    "Crie Posts Fixos, Carrosséis ou Vídeos curtos."
)

# Leitura das Chaves de API do Streamlit Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
pexels_key = st.secrets.get("PEXELS_API_KEY", "")

with st.sidebar:
    st.header("⚙️ Status")
    if gemini_key:
        st.success("⚡ Autenticado com sucesso!")
    else:
        st.error("⚠️ Defina as chaves em Settings > Secrets.")

# Formulário Principal
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
        if tipo_formato == "Carrossel":
            num_slides = st.slider("Quantidade de slides:", 3, 7, 5)
        else:
            num_slides = 3

    btn_gerar = st.form_submit_button("🚀 Gerar Conteúdo Completo")


# --- FUNÇÕES AUXILIARES ---


def limpar_json_resposta(texto):
    """Trata e limpa a resposta textual do LLM para evitar erros de parse JSON."""
    texto = re.sub(r"^```json\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^```\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"```$", "", texto, flags=re.MULTILINE)
    return texto.strip()


def buscar_video_pexels(query, api_key):
    if not api_key:
        return None
    url = f"[https://api.pexels.com/videos/search?query=](https://api.pexels.com/videos/search?query=){urllib.parse.quote(query)}&per_page=1&orientation=portrait"
    headers = {"Authorization": api_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
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


def gerar_url_imagem(prompt, aspecto="1080x1080"):
    w, h = aspecto.split("x")
    prompt_limpo = urllib.parse.quote(f"{prompt}, professional photography, high quality")
    return f"[https://image.pollinations.ai/prompt/](https://image.pollinations.ai/prompt/){prompt_limpo}?width={w}&height={h}&nologo=true"


def processar_video_sincronizado(cenas, pexels_key):
    """Gera o áudio de cada cena, baixa os vídeos correspondentes e junta tudo sincronizado."""
    clips = []
    arquivos_temp = []

    try:
        for idx, cena in enumerate(cenas):
            narracao = cena.get("narracao", "")
            busca = cena.get("busca_pexels", "sports")

            # 1. Gerar Áudio da Cena
            tts = gTTS(text=narracao, lang="pt", tld="com.br")
            f_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(f_audio.name)
            f_audio.close()
            arquivos_temp.append(f_audio.name)
            audio_clip = AudioFileClip(f_audio.name)

            # 2. Buscar Vídeo no Pexels
            url_vid = buscar_video_pexels(busca, pexels_key)
            if not url_vid:
                url_vid = buscar_video_pexels("fitness", pexels_key)

            if url_vid:
                resp_vid = requests.get(url_vid)
                f_vid = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                f_vid.write(resp_vid.content)
                f_vid.close()
                arquivos_temp.append(f_vid.name)

                video_clip = VideoFileClip(f_vid.name)

                # Sincronizar duração do corte com a duração exata do áudio
                duracao_audio = audio_clip.duration
                if video_clip.duration < duracao_audio:
                    video_clip = video_clip.loop(duration=duracao_audio)
                else:
                    video_clip = video_clip.subclip(0, duracao_audio)

                video_clip = video_clip.set_audio(audio_clip)
                clips.append(video_clip)

        if clips:
            video_final = concatenate_videoclips(clips, method="compose")
            f_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
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
        return None

    finally:
        # Limpeza de arquivos temporários do servidor
        for f_path in arquivos_temp:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception:
                    pass


# --- LÓGICA PRINCIPAL ---

if btn_gerar:
    if not gemini_key:
        st.error("Chave do Gemini ausente. Configure nos Secrets.")
    elif not tema:
        st.warning("Informe o tema para prosseguir.")
    else:
        with st.spinner("🤖 A IA está produzindo o conteúdo..."):
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-3.6-flash")

                if tipo_formato == "Post Fixo":
                    prompt_sistema = f"""
                    Crie um Post Fixo sobre: {tema}. Público: {publico}. Tom: {tom}.
                    Retorne estritamente um JSON estruturado como neste exemplo:
                    {{
                        "titulo_imagem": "Frase de impacto para a imagem",
                        "prompt_imagem": "Prompt em inglês para imagem fotográfica",
                        "legenda": "Legenda completa com hashtags"
                    }}
                    """

                elif tipo_formato == "Carrossel":
                    prompt_sistema = f"""
                    Crie um Carrossel de {num_slides} slides sobre: {tema}. Público: {publico}. Tom: {tom}.
                    Retorne estritamente um JSON estruturado como neste exemplo sem quebras de linha nas strings:
                    {{
                        "slides": [
                            {{
                                "numero": 1,
                                "texto_slide": "Texto explicativo do slide",
                                "prompt_imagem": "Prompt em inglês para fundo visual"
                            }}
                        ],
                        "legenda": "Legenda do post"
                    }}
                    """

                else:  # Vídeo
                    prompt_sistema = f"""
                    Crie um roteiro dividido em cenas curtas para vídeo sobre: {tema}. Público: {publico}. Tom: {tom}.
                    Cada cena deve ter uma narração direta e palavras-chave em inglês para busca no Pexels.
                    Retorne estritamente um JSON estruturado como neste exemplo:
                    {{
                        "cenas": [
                            {{
                                "numero": 1,
                                "narracao": "Frase de fala da cena",
                                "busca_pexels": "runner exercise"
                            }},
                            {{
                                "numero": 2,
                                "narracao": "Segunda frase da narração",
                                "busca_pexels": "gym leg press"
                            }}
                        ],
                        "legenda": "Legenda completa para redes sociais"
                    }}
                    """

                response = model.generate_content(
                    prompt_sistema,
                    generation_config={"response_mime_type": "application/json"},
                )

                json_limpo = limpar_json_resposta(response.text)
                dados = json.loads(json_limpo)

                st.success("✨ Conteúdo gerado com sucesso!")

                # Exibição - Post Fixo
                if tipo_formato == "Post Fixo":
                    c1, c2 = st.columns(2)
                    with c1:
                        url_img = gerar_url_imagem(dados.get("prompt_imagem", tema))
                        st.image(url_img, use_container_width=True)
                        st.info(f"💡 **Texto na Imagem:** {dados.get('titulo_imagem')}")
                        img_bytes = requests.get(url_img).content
                        st.download_button(
                            "📥 Baixar Imagem", img_bytes, "post_fixo.jpg", "image/jpeg"
                        )
                    with c2:
                        st.subheader("📝 Legenda")
                        st.text_area("Copie o texto:", dados.get("legenda"), height=300)

                # Exibição - Carrossel
                elif tipo_formato == "Carrossel":
                    slides = dados.get("slides", [])
                    cols = st.columns(len(slides))
                    for idx, slide in enumerate(slides):
                        with cols[idx]:
                            st.markdown(f"**Slide {slide['numero']}**")
                            url_img = gerar_url_imagem(slide.get("prompt_imagem", tema))
                            st.image(url_img, use_container_width=True)
                            st.caption(slide.get("texto_slide"))
                            img_bytes = requests.get(url_img).content
                            st.download_button(
                                f"📥 Slide {slide['numero']}",
                                img_bytes,
                                f"slide_{slide['numero']}.jpg",
                                "image/jpeg",
                            )

                    st.divider()
                    st.subheader("📝 Legenda")
                    st.text_area("Copie o texto:", dados.get("legenda"), height=250)

                # Exibição - Vídeo Sincronizado
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("🎬 Vídeo Editado com Áudio e Cortes")
                        cenas = dados.get("cenas", [])

                        with st.spinner(
                            "🎥 Renderizando cortes de vídeo e sincronizando o áudio..."
                        ):
                            video_bytes = processar_video_sincronizado(cenas, pexels_key)

                        if video_bytes:
                            st.video(video_bytes)
                            st.download_button(
                                "📥 Baixar Vídeo Completo (MP4)",
                                video_bytes,
                                "video_editado.mp4",
                                "video/mp4",
                            )
                        else:
                            st.error(
                                "Erro ao renderizar o vídeo. Verifique se a chave do Pexels está ativa."
                            )

                    with c2:
                        st.subheader("🗣️ Cortes e Roteiro")
                        for cena in cenas:
                            st.write(
                                f"**Cena {cena.get('numero')}:** {cena.get('narracao')}"
                            )
                            st.caption(f"Visual: `{cena.get('busca_pexels')}`")
                        st.divider()
                        st.subheader("📝 Legenda do Vídeo")
                        st.text_area("Copie o texto:", dados.get("legenda"), height=200)

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")
