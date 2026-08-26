import json
import urllib.parse
import google.generativeai as genai
import requests
import streamlit as st

# Configuração da página Web
st.set_page_config(
    page_title="Gerador de Conteúdo IA",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎬 Gerador Inteligente de Roteiros e Mídias")
st.markdown(
    "Crie roteiros dinâmicos para vídeos curtos (Reels/TikTok/Shorts) com sugestões de vídeos e capa por IA."
)

# Sidebar para chaves de API
with st.sidebar:
    st.header("⚙️ Configurações")
    gemini_key = st.text_input("Chave Gemini API", type="password")
    pexels_key = st.text_input("Chave Pexels API", type="password")
    st.info("💡 As chaves são gratuitas e não requerem cartão de crédito.")

# Formulário Principal
with st.form("form_conteudo"):
    col1, col2 = st.columns(2)
    with col1:
        tema = st.text_input(
            "Tema do vídeo:",
            placeholder="Ex: 3 benefícios da quiropraxia para corredores",
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
        duracao = st.select_slider(
            "Duração aproximada:",
            options=["15 segundos (3 cenas)", "30 segundos (5 cenas)", "60 segundos (8 cenas)"],
        )

    btn_gerar = st.form_submit_button("🚀 Gerar Roteiro e Mídias")

# Função para buscar vídeo no Pexels
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
                # Busca por um arquivo de qualidade HD/SD em MP4
                for v in video_files:
                    if v.get("file_type") == "video/mp4":
                        return v.get("link")
    except Exception:
        pass
    return None

# Função para gerar imagem via Pollinations.ai (Sem API Key)
def gerar_url_imagem(prompt):
    prompt_limpo = urllib.parse.quote(f"{prompt}, high quality, photorealistic, 4k")
    return f"https://image.pollinations.ai/prompt/{prompt_limpo}?width=1080&height=1920&nologo=true"

# Lógica de Geração
if btn_gerar:
    if not gemini_key:
        st.error("Por favor, insira sua chave do Gemini na barra lateral.")
    elif not tema:
        st.warning("Por favor, digite um tema para o vídeo.")
    else:
        with st.spinner("🤖 A IA está escrevendo o roteiro e selecionando mídias..."):
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                prompt_sistema = f"""
                Você é um estrategista de conteúdo para mídias sociais especializado em vídeos curtos.
                Crie um roteiro para um vídeo com as seguintes especificações:
                - Tema: {tema}
                - Tom: {tom}
                - Público-alvo: {publico}
                - Formato: {duracao}

                IMPORTANTE: Responda EXCLUSIVAMENTE em formato JSON com a seguinte estrutura:
                {{
                    "titulo": "Título chamativo do post",
                    "descricao_capa": "Prompt curto em INGLÊS para gerar uma imagem de capa fotográfica e realista sobre o tema",
                    "cenas": [
                        {{
                            "numero": 1,
                            "narracao": "Texto da locução ou legenda da cena",
                            "busca_pexels": "2 a 3 palavras-chave em INGLÊS para buscar um vídeo de stock no Pexels relativo a esta cena"
                        }}
                    ]
                }}
                """

                response = model.generate_content(
                    prompt_sistema,
                    generation_config={"response_mime_type": "application/json"},
                )
                dados = json.loads(response.text)

                st.success("✨ Roteiro gerado com sucesso!")

                # Exibição do Título e Capa
                st.subheader(f"📌 {dados.get('titulo')}")

                col_capa, col_info = st.columns([1, 2])
                with col_capa:
                    url_capa = gerar_url_imagem(dados.get("descricao_capa", tema))
                    st.image(url_capa, caption="Sugestão de Capa (IA)", use_container_width=True)
                with col_info:
                    st.markdown("**Estratégia de Capa:**")
                    st.write(dados.get("descricao_capa"))

                st.divider()
                st.subheader("🎬 Cenas do Roteiro e Mídias Recomendadas")

                # Iteração pelas cenas
                for cena in dados.get("cenas", []):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"### Cena {cena['numero']}")
                        st.write(f"🗣️ **Locução / Legenda:** {cena['narracao']}")
                        st.caption(f"🔍 Busca Pexels: `{cena['busca_pexels']}`")

                    with c2:
                        url_video = buscar_video_pexels(cena["busca_pexels"], pexels_key)
                        if url_video:
                            st.video(url_video)
                        else:
                            st.info("Vídeo de demonstração indisponível ou chave Pexels ausente.")
                    st.divider()

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar: {e}")