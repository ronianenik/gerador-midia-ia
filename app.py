import io
import json
import urllib.parse
from gtts import gTTS
import google.generativeai as genai
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
    "Crie Posts Fixos, Carrosséis ou Vídeos completos com mídias, áudio em MP3 e legendas prontas para publicação."
)

# Sidebar para chaves de API
with st.sidebar:
    st.header("⚙️ Configurações")
    gemini_key = st.secrets["AIzaSyCOTIZNTzcTgQbpcg6wGilfZk1gx5XsRJU"]
    pexels_key = st.secrets["hd5W7fD9lT59927KHdfAiumi2p3Tk4jgtOIgAp2ZWLt38CbnUNGQQ4av"]
    st.info("💡 As chaves são gratuitas e não requerem cartão de crédito.")

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
            placeholder="Ex: 3 benefícios da musculação para corredores",
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
            "Público-alvo:", placeholder="Ex: Atletas amadores e praticantes de corrida"
        )
        if tipo_formato == "Carrossel":
            num_slides = st.slider("Quantidade de slides:", 3, 7, 5)
        else:
            num_slides = 5

    btn_gerar = st.form_submit_button("🚀 Gerar Conteúdo Completo")


# --- FUNÇÕES AUXILIARES ---


# Busca de Vídeo no Pexels
def buscar_video_pexels(query, api_key):
    if not api_key:
        return None
    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=1&orientation=portrait"
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


# Geração de Imagem via Pollinations.ai (Grátis)
def gerar_url_imagem(prompt, aspecto="1080x1080"):
    w, h = aspecto.split("x")
    prompt_limpo = urllib.parse.quote(f"{prompt}, high quality, professional photography, 4k")
    return f"https://image.pollinations.ai/prompt/{prompt_limpo}?width={w}&height={h}&nologo=true"


# Geração de Áudio com gTTS (Grátis)
def gerar_audio_mp3(texto):
    tts = gTTS(text=texto, lang="pt", tld="com.br")
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp


# --- LÓGICA DE PROCESSAMENTO ---

if btn_gerar:
    if not gemini_key:
        st.error("Por favor, insira sua chave do Gemini na barra lateral.")
    elif not tema:
        st.warning("Por favor, digite um tema para o conteúdo.")
    else:
        with st.spinner("🤖 A IA está criando o conteúdo e preparando as mídias..."):
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-2.5-flash")

                # Ajuste de prompts dependendo do formato escolhido
                if tipo_formato == "Post Fixo":
                    prompt_sistema = f"""
                    Crie um Post Fixo para Instagram sobre: {tema}.
                    Público: {publico}. Tom: {tom}.
                    Responda EXCLUSIVAMENTE em JSON:
                    {{
                        "titulo_imagem": "Texto curto e chamativo (Headline) para a imagem",
                        "prompt_imagem": "Prompt em INGLÊS para gerar a imagem de fundo fotográfica sobre o tema",
                        "legenda": "Legenda completa do post com emojis e hashtags pertinentes"
                    }}
                    """

                elif tipo_formato == "Carrossel":
                    prompt_sistema = f"""
                    Crie um Carrossel de {num_slides} slides sobre: {tema}.
                    Público: {publico}. Tom: {tom}.
                    Responda EXCLUSIVAMENTE em JSON:
                    {{
                        "slides": [
                            {{
                                "numero": 1,
                                "texto_slide": "Texto principal do slide",
                                "prompt_imagem": "Prompt em INGLÊS para gerar imagem de fundo para este slide"
                            }}
                        ],
                        "legenda": "Legenda completa do post para carrossel com chamada para ação, emojis e hashtags"
                    }}
                    """

                else:  # Vídeo
                    prompt_sistema = f"""
                    Crie um roteiro de Vídeo curto (Reels/TikTok) sobre: {tema}.
                    Público: {publico}. Tom: {tom}.
                    Responda EXCLUSIVAMENTE em JSON:
                    {{
                        "texto_narracao": "Texto contínuo da narração/locução do vídeo para ser transformado em áudio",
                        "busca_pexels": "2 palavras-chave em INGLÊS para buscar um vídeo de stock no Pexels",
                        "legenda": "Legenda completa do vídeo com chamada para ação, emojis e hashtags"
                    }}
                    """

                response = model.generate_content(
                    prompt_sistema,
                    generation_config={"response_mime_type": "application/json"},
                )
                dados = json.loads(response.text)

                st.success("✨ Conteúdo gerado com sucesso!")

                # --- EXIBIÇÃO: POST FIXO ---
                if tipo_formato == "Post Fixo":
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.subheader("🖼️ Imagem do Post")
                        url_img = gerar_url_imagem(dados.get("prompt_imagem"))
                        st.image(url_img, use_container_width=True)
                        st.info(f"💡 **Texto Sugerido na Imagem:** {dados.get('titulo_imagem')}")

                        # Botão de download da imagem
                        img_bytes = requests.get(url_img).content
                        st.download_button(
                            "📥 Baixar Imagem", img_bytes, "post_fixo.jpg", "image/jpeg"
                        )

                    with c2:
                        st.subheader("📝 Legenda Pronta")
                        st.text_area(
                            "Copie e cole no Instagram:",
                            dados.get("legenda"),
                            height=350,
                        )

                # --- EXIBIÇÃO: CARROSSEL ---
                elif tipo_formato == "Carrossel":
                    st.subheader("🎨 Slides do Carrossel")
                    slides = dados.get("slides", [])
                    cols = st.columns(len(slides))

                    for idx, slide in enumerate(slides):
                        with cols[idx]:
                            st.markdown(f"**Slide {slide['numero']}**")
                            url_img = gerar_url_imagem(slide.get("prompt_imagem"))
                            st.image(url_img, use_container_width=True)
                            st.caption(f"✍️ {slide.get('texto_slide')}")

                            # Botão para baixar slide
                            img_bytes = requests.get(url_img).content
                            st.download_button(
                                f"📥 Baixar #{slide['numero']}",
                                img_bytes,
                                f"slide_{slide['numero']}.jpg",
                                "image/jpeg",
                            )

                    st.divider()
                    st.subheader("📝 Legenda do Carrossel")
                    st.text_area(
                        "Copie e cole no Instagram:", dados.get("legenda"), height=250
                    )

                # --- EXIBIÇÃO: VÍDEO ---
                else:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.subheader("🎬 Vídeo de Stock Recomendado")
                        url_vid = buscar_video_pexels(dados.get("busca_pexels"), pexels_key)
                        if url_vid:
                            st.video(url_vid)
                            vid_bytes = requests.get(url_vid).content
                            st.download_button(
                                "📥 Baixar Vídeo MP4", vid_bytes, "video_stock.mp4", "video/mp4"
                            )
                        else:
                            st.info(
                                "Insira a chave do Pexels na barra lateral para carregar o vídeo de fundo."
                            )

                        st.subheader("🎙️ Narração do Vídeo (Áudio em Português)")
                        audio_fp = gerar_audio_mp3(dados.get("texto_narracao"))
                        st.audio(audio_fp, format="audio/mp3")
                        st.download_button(
                            "📥 Baixar Áudio MP3", audio_fp, "narracao.mp3", "audio/mp3"
                        )

                    with c2:
                        st.subheader("🗣️ Roteiro da Narração")
                        st.write(dados.get("texto_narracao"))
                        st.divider()
                        st.subheader("📝 Legenda do Vídeo")
                        st.text_area(
                            "Copie e cole nas redes:", dados.get("legenda"), height=250
                        )

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")