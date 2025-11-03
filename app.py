import streamlit as st
import json
import subprocess
import shlex
import os
import streamlit.components.v1 as components
import base64

# --- 1. Configuración de la Página ---
# layout="wide" asegura el ancho total
st.set_page_config(
    page_title="Estación de Pago 3.0",
    layout="wide",
    initial_sidebar_state="collapsed", 
    page_icon="/images/EPicon.ico"
)

# Inicializar estado para la vista actual
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'menu' 
if 'content_file' not in st.session_state:
    st.session_state.content_file = ''
if 'construction_title' not in st.session_state:
    st.session_state.construction_title = "Información"
if 'construction_image' not in st.session_state:
    st.session_state.construction_image = ''
if 'needs_rerun' not in st.session_state:
    st.session_state.needs_rerun = False


# --- FUNCIÓN DE UTILIDAD: Convertir imagen a Base64 para incrustar en HTML ---
def img_to_base64_uri(file_path):
    """Convierte una imagen local a Base64 Data URI."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, file_path)
        
        # Determinar el MIME type
        mime_type = 'image/png' 
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        elif file_path.lower().endswith(('.gif')):
            mime_type = 'image/gif'
        elif file_path.lower().endswith(('.ico')):
            mime_type = 'image/x-icon'

        with open(full_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        return f"data:{mime_type};base64,{encoded_string}"
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


# --- 2. Carga de URLs desde JSON ---
def load_urls():
    try:
        with open('urls.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ ERROR CRÍTICO: No se encontró el archivo `urls.json`. Asegúrate de que esté en el mismo directorio.")
        return None
    except json.JSONDecodeError:
        st.error("❌ ERROR CRÍTICO: El archivo `urls.json` está mal formado y no se puede leer.")
        return None

URLS = load_urls()

# --- 3. Definición de Servicios (Ajustar RUTAS A TUS IMÁGENES LOCALES) ---
SERVICES = [
    {'id': 'recargas', 'title': 'RECARGAS', 'imageUrl': 'images/recargas.png'},
    {'id': 'remesas', 'title': 'REMESAS A VENEZUELA', 'imageUrl': 'images/remesas.png'},
    {'id': 'transporte', 'title': 'TARJETAS PARA TRANSPORTE', 'imageUrl': 'images/transporte.png'},
    {'id': 'pago_servicios', 'title': 'PAGO DE SERVICIOS', 'imageUrl': 'images/pago_servicios.png'},
    {'id': 'paqwallet', 'title': 'RECARGAS PAQWALLET', 'imageUrl': 'images/paqwallet.png'},
    {'id': 'entradas', 'title': 'ENTRADAS EVENTOS', 'imageUrl': 'images/entradas.png'},
    {'id': 'seguros', 'title': 'SEGUROS', 'imageUrl': 'images/seguros.png'},
    {'id': 'loteria', 'title': 'LOTERÍA', 'imageUrl': 'images/loteria.png'},
]

# --- 4. Funciones de Acción y Flujo ---
def run_local_program(command: str):
    """Ejecuta un programa local."""
    try:
        parts = shlex.split(command)
        if not os.path.isabs(parts[0]):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            combined_path = os.path.join(script_dir, parts[0])
            parts[0] = os.path.normpath(combined_path)
            
        subprocess.Popen(parts, shell=False) 
        st.toast(f"✅ Ejecutando: {parts[0]}...", icon="💻")
        
    except FileNotFoundError:
        st.error(f"❌ Error: El programa no se encontró en la ruta: {parts[0]}")
    except Exception as e:
        st.error(f"❌ Error al ejecutar el programa '{command}': {e}")

def get_service_action(service_id: str):
    """Determina la acción (URL, EXE, HTML local o Construcción)."""
    if not URLS:
        return {'type': 'error', 'value': 'Diccionario de URLs no cargado.'}
        
    url = URLS.get(service_id)
    
    if not isinstance(url, str) or not url:
        return {'type': 'error', 'value': f"URL no encontrada o inválida para: {service_id}"}

    cleaned_url = url.strip()

    if cleaned_url.lower() == "encontruccion.html":
        return {'type': 'construction_message', 'value': service_id}
    
    if cleaned_url.lower().startswith(('http://', 'https://')):
        return {'type': 'external_url', 'value': cleaned_url}
    
    program_path = shlex.split(cleaned_url)[0].lower()
    
    if program_path.endswith(('.exe', '.bat', '.cmd', '.sh')):
        return {'type': 'program', 'value': cleaned_url}

    if cleaned_url.lower().endswith('.html'):
         return {'type': 'local_html', 'value': cleaned_url}

    st.warning(f"Acción no reconocida para '{service_id}': {url}. Tratando como HTML local.")
    return {'type': 'local_html', 'value': cleaned_url}


def set_view_content_html(file_path):
    st.session_state.current_view = 'content_html'
    st.session_state.content_file = file_path 
    st.session_state.needs_rerun = True

def set_view_construction_message(service_id):
    """Establece el estado para ir a la vista de construcción, guarda la imagen y marca la necesidad de rerun."""
    st.session_state.current_view = 'content_construction'
    service_info = next((s for s in SERVICES if s['id'].lower() == service_id.lower()), None)
    
    if service_info:
        st.session_state.construction_title = service_info['title']
        st.session_state.construction_image = service_info['imageUrl'] 
    else:
        st.session_state.construction_title = "Información"
        st.session_state.construction_image = ""
        
    st.session_state.needs_rerun = True


def render_html_file(file_path):
    """Muestra el contenido de un archivo HTML local."""
    
    if st.button("⬅️ Volver al Menú", key="back_to_menu_btn", type="primary"): 
        st.session_state.current_view = 'menu'
        st.session_state.content_file = ''
        st.rerun()

    service_id_from_file = file_path.replace('.html', '').lower()
    service_info = next((s for s in SERVICES if s['id'].lower() == service_id_from_file), None)
    title = service_info['title'] if service_info else "Información"

    st.header(title)
    st.divider()

    html_to_render = ""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path_to_check = os.path.join(script_dir, file_path) 
    
    try:
        if not os.path.exists(full_path_to_check):
            st.error(f"❌ Error: Archivo HTML no encontrado en la ruta: {full_path_to_check}")
            html_to_render = f"<div style='color: red;'>Error: Contenido no disponible. Archivo '{file_path}' no encontrado.</div>"
        else:
            with open(full_path_to_check, 'r', encoding='utf-8') as f:
                html_to_render = f.read()
    except Exception as e:
        st.error(f"❌ Error al leer el archivo HTML '{full_path_to_check}': {e}")
        html_to_render = f"<div style='color: red;'>Error al cargar el contenido: {e}</div>"
    
    components.html(html_to_render, height=1500, scrolling=True) 

# --- FUNCIÓN DE CONSTRUCCIÓN (CON IMAGEN EN BASE64) ---
def render_construction_page():
    
    image_uri = ""
    if st.session_state.construction_image:
        image_uri = img_to_base64_uri(st.session_state.construction_image)

    image_html = ""
    if image_uri:
        image_html = f"""
            <img src="{image_uri}" style="
                width: 120px; 
                height: 120px; 
                object-fit: contain; 
                margin-bottom: 30px; 
                border-radius: 10px; 
                border: 3px solid #EE7518;
            ">
        """
    
    html_to_render = f"""
        <style>
            /* Estilos para asegurar que el contenido ocupe todo el espacio del iframe */
            html, body {{
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden; 
            }}
            /* Contenedor principal: Flexbox para centrado vertical y horizontal */
            .main-container {{
                text-align: center; 
                min-height: 100vh; 
                display: flex;
                flex-direction: column;
                justify-content: center; 
                align-items: center; 
                padding: 20px;
                box-sizing: border-box; 
                background-color: #f0f2f6;
            }}
            /* Caja del mensaje: Responsiva */
            .message-box {{
                background-color: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 8px 25px rgba(0,0,0,0.2); 
                max-width: 650px; 
                width: 100%; 
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                align-items: center; 
            }}
            @media (max-width: 768px) {{
                .message-box {{
                    padding: 30px 20px;
                }}
            }}
        </style>
        
        <div class="main-container">
            <div class="message-box">
                {image_html} 
                <h1 style="color: #333; font-size: 2.8em; margin-bottom: 20px;">
                    ¡SERVICIO EN CONSTRUCCIÓN!
                </h1>
                <p style="color: #EE7518; font-size: 1.8em; font-weight: bold; margin-bottom: 25px;">
                    {st.session_state.construction_title}
                </p>
                <p style="color: #666; font-size: 1.2em; line-height: 1.6;">
                    Estamos trabajando arduamente para que esta opción esté disponible pronto.
                    Agradecemos tu paciencia y comprensión.
                </p>
                <div style="margin-top: 40px;">
                    <button 
                        id="backButton"
                        style="
                            background-color: #EE7518;
                            color: white;
                            padding: 15px 30px;
                            border: none;
                            border-radius: 8px;
                            font-size: 1.3em;
                            cursor: pointer;
                            transition: background-color 0.3s ease;
                        "
                    >
                        ⬅️ Volver al Menú Principal (<span id="countdown">60</span>s)
                    </button>
                </div>
            </div>
        </div>

        <script>
            let countdown = 60;
            const countdownElement = document.getElementById('countdown');
            const backButton = document.getElementById('backButton');

            // CIERRE LIMPIO: FUERZA RECARGA TOTAL
            function returnToMenu() {{
                window.location.href = window.location.origin; 
            }}

            let timer = setInterval(() => {{
                countdown--;
                if (countdownElement) {{
                    countdownElement.textContent = countdown;
                }}
                if (countdown <= 0) {{
                    clearInterval(timer);
                    returnToMenu();
                }}
            }}, 1000);

            if (backButton) {{
                backButton.addEventListener('click', () => {{
                    clearInterval(timer); 
                    returnToMenu();
                }});
            }}
        </script>
    """
    
    components.html(html_to_render, height=850, scrolling=False) 
    

# --- 5. Componente de Estilos (CSS para Pantalla Completa) ---
def apply_custom_styles():
    st.markdown(
        """
        <style>
            /* ------------------------------------------------ */
            /* CSS para PANTALLA COMPLETA (Maximiza el contenido) */
            /* ------------------------------------------------ */
            
            /* 1. Oculta el encabezado/menú de Streamlit (los 3 puntos y el botón de compartir) */
            header {
                display: none !important;
            }

            /* 2. Oculta el botón de la barra lateral (si existiera) */
            [data-testid="stSidebar"] {
                display: none;
            }

            /* 3. Elimina el padding de Streamlit en el contenedor principal */
            .main {
                padding-top: 0px !important;
                padding-right: 0px !important;
                padding-left: 0px !important;
                padding-bottom: 0px !important;
            }

            /* 4. Asegura que el contenedor de la vista principal ocupe todo el espacio vertical */
            [data-testid="stAppViewContainer"] {
                padding-top: 0px !important;
                padding-bottom: 0px !important;
                min-height: 100vh; /* Ocupa la altura completa del viewport */
            }

            /* 5. Asegura que la barra de progreso de carga superior no arruine la vista */
            [data-testid="stStatusWidget"] {
                display: none;
            }

            /* ------------------------------------------------ */
            /* Estilos Específicos de la App */
            /* ------------------------------------------------ */
            
            .header-container {
                display: flex;
                align-items: center;
                padding-top: 10px;
                padding-bottom: 5px;
            }
            .header-text-block {
                margin-left: 15px;
            }
            .header-title {
                font-size: 3.8em; 
                font-weight: bold;
                color: #EE7518; 
                line-height: 1.1; 
            }
            .header-subtitle {
                font-size: 2.2em; 
                font-weight: medium;
                color: #EE7518; 
                /* LÍNEA NARANJA ELIMINADA */
                border-top: none; 
                padding-top: 5px;
                margin-top: 10px; 
                margin-bottom: 20px; 
            }

            .stImage > img {
                max-height: 80px; 
                width: auto;
                object-fit: contain;
            }

            hr[data-testid="stDivider"] {
                border: none;
                height: 1px;
                background-color: #e0e0e0; 
            }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 6. Componente Header ---
def Header():
    col_logo, col_text = st.columns([0.12, 0.88]) 
    
    with col_logo:
        st.image("images/logo.png", width=80) 
        
    with col_text:
        st.markdown(
            """
            <div class="header-text-block">
                <p class="header-title">ESTACIÓN DE PAGO 3.0</p> 
                <p class="header-subtitle">Innovando la experiencia del usuario</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    

# --- 7. Componente ServiceCard ---
def ServiceCard(service: dict, action: dict):
    
    with st.container(border=True):
        
        st.image(service['imageUrl'], use_container_width=True) 

        action_type = action['type']
        action_value = action['value']
        button_key = f"btn_{service['id']}" 
        button_label = service['title'] 
        
        button_type = "primary" 
        
        if action_type == 'external_url':
            st.link_button(button_label, url=action_value, use_container_width=True, type=button_type)
        
        elif action_type == 'program':
            st.button(
                button_label, 
                key=button_key, 
                use_container_width=True, 
                on_click=run_local_program, 
                args=(action_value,),
                type=button_type
            )
        
        elif action_type == 'construction_message':
            if st.button(
                button_label, 
                key=button_key, 
                use_container_width=True, 
                type=button_type
            ):
                set_view_construction_message(action_value)

        elif action_type == 'local_html':
            if st.button(
                button_label, 
                key=button_key, 
                use_container_width=True, 
                type=button_type
            ):
                set_view_content_html(action_value)
        
        else:
            st.button(
                f"{button_label} (No Disp.)", 
                key=f"{button_key}_disabled",
                use_container_width=True, 
                disabled=True,
                type="secondary"
            )
            if action_type == 'error':
                 st.caption(f"Error: {action_value}")


# --- 8. Layout Principal de la Aplicación ---
def main_app():
    apply_custom_styles() 
    
    if not URLS:
        st.error("La aplicación no puede iniciar porque `urls.json` no se cargó correctamente.")
        st.stop()
    
    if st.session_state.current_view == 'menu':
        Header()
        cols = st.columns(4)
        for i, service in enumerate(SERVICES):
            with cols[i % 4]: 
                service_action = get_service_action(service['id'])
                ServiceCard(service, service_action)
    
    elif st.session_state.current_view == 'content_html':
        Header() 
        render_html_file(st.session_state.content_file)
        
    elif st.session_state.current_view == 'content_construction':
        render_construction_page()
    
    # Ejecuta rerun si el estado cambió
    if st.session_state.needs_rerun:
        st.session_state.needs_rerun = False
        st.rerun()


# --- Ejecución del Script ---
if __name__ == "__main__":
    main_app()