import streamlit as st
import json
import subprocess
import shlex
import os
import streamlit.components.v1 as components

# --- 1. Configuración de la Página ---
st.set_page_config(
    page_title="Estación de Pago 3.0", # Título de la pestaña/ventana
    layout="wide",
    initial_sidebar_state="collapsed", 
)

# Inicializar estado para la vista (menú o contenido)
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'menu' # 'menu' o 'content'
if 'content_file' not in st.session_state:
    st.session_state.content_file = ''

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

# --- 3. Definición de Servicios (con imágenes locales) ---
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

# --- 4. Funciones de Acción ---

def run_local_program(command: str):
    """Ejecuta un programa local en la máquina que aloja Streamlit (Servidor)."""
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
    """Determina si la acción es una URL externa, un programa local o un archivo HTML local."""
    if not URLS:
        return {'type': 'error', 'value': 'Diccionario de URLs no cargado.'}
        
    url = URLS.get(service_id)
    
    if not isinstance(url, str) or not url:
        return {'type': 'error', 'value': f"URL no encontrada o inválida para: {service_id}"}

    cleaned_url = url.strip()

    # Patrón 1: URL web externa (http, https)
    if cleaned_url.lower().startswith(('http://', 'https://')):
        return {'type': 'external_url', 'value': cleaned_url}
    
    # Patrón 2: Programa local (basado en extensión)
    program_path = shlex.split(cleaned_url)[0].lower()
    
    if program_path.endswith(('.exe', '.bat', '.cmd', '.sh')):
        return {'type': 'program', 'value': cleaned_url}

    # Patrón 3: Archivo HTML local (termina en .html)
    if cleaned_url.lower().endswith('.html'):
         return {'type': 'local_html', 'value': cleaned_url}

    st.warning(f"Acción no reconocida para '{service_id}': {url}. Tratando como HTML local.")
    return {'type': 'local_html', 'value': cleaned_url}


def display_local_html(file_path):
    """Cambia el estado para renderizar el contenido HTML local."""
    st.session_state.current_view = 'content'
    st.session_state.content_file = file_path
    st.rerun()

def render_html_content(file_path):
    """Muestra el contenido del archivo HTML local en la aplicación."""
    
    if st.button("⬅️ Volver al Menú", key="back_to_menu_btn", type="primary"): 
        st.session_state.current_view = 'menu'
        st.session_state.content_file = ''
        st.rerun()

    service_id_from_file = file_path.replace('.html', '')
    service_info = next((s for s in SERVICES if s['id'] == service_id_from_file), None)
    title = service_info['title'] if service_info else f"Contenido: {file_path}"
    
    st.header(title)
    st.divider()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, file_path)
        
        if not os.path.exists(full_path):
            html_content = f"""
                <div style="text-align: center; padding: 50px; background-color: #f9f9f9; border-radius: 10px; border: 1px solid #ddd;">
                    <h2 style="color: #333; font-size: 2em;">{title}</h2>
                    <p style="color: #EE7518; font-size: 1.5em; font-weight: bold;">¡SERVICIO EN CONSTRUCCIÓN!</p>
                    <p style="color: #666; margin-top: 15px;">Estamos trabajando para que esta opción esté disponible pronto.</p>
                </div>
            """
        else:
            with open(full_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        components.html(html_content, height=1500, scrolling=True) 
        
    except Exception as e:
        st.error(f"❌ Error al leer o renderizar el archivo HTML '{file_path}': {e}")


# --- 5. Componente de Estilos ---
def apply_custom_styles():
    st.markdown(
        """
        <style>
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
                font-size: 2.8em; 
                font-weight: bold;
                color: #EE7518; 
                line-height: 1.2; 
            }
            .header-subtitle {
                font-size: 1.5em; 
                font-weight: medium;
                color: #EE7518; 
                border-top: 1px solid rgba(238, 117, 24, 0.3);
                padding-top: 5px;
                margin-top: 5px; 
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

# --- 6. Componente Header (Contenido con título actualizado) ---
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
    
    st.divider()
    

# --- 7. Componente ServiceCard (Botones Naranja) ---
def ServiceCard(service: dict, action: dict):
    """
    Renderiza la tarjeta de servicio con imagen y botón de acción.
    """
    
    with st.container(border=True):
        
        # 1. Imagen 
        st.image(service['imageUrl'], use_container_width=True) 

        # 2. Botón de Acción
        action_type = action['type']
        action_value = action['value']
        button_key = f"btn_{service['id']}" 
        button_label = service['title'] 
        
        # Uso 'primary' para que el fondo sea naranja en todos los casos
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
                type=button_type # <-- CAMBIO CLAVE AQUÍ
            )
        
        elif action_type == 'local_html':
            st.button(
                button_label, 
                key=button_key, 
                use_container_width=True, 
                on_click=display_local_html, 
                args=(action_value,),
                type=button_type # <-- CAMBIO CLAVE AQUÍ
            )
        
        else: # 'error' o tipo no soportado
            # Los botones deshabilitados NO se pueden hacer de color primario en Streamlit sin CSS, 
            # así que mantendremos el estilo secundario aquí.
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
    
    Header()

    if not URLS:
        st.error("La aplicación no puede iniciar porque `urls.json` no se cargó correctamente.")
        st.stop()
    
    # ----------------------------------------------------
    # LÓGICA DE VISTA: Menú principal vs. Contenido HTML
    # ----------------------------------------------------
    if st.session_state.current_view == 'content':
        render_html_content(st.session_state.content_file)
    else:
        # Muestra el menú principal (la cuadrícula de tarjetas)
        cols = st.columns(4)
        
        for i, service in enumerate(SERVICES):
            with cols[i % 4]: 
                service_action = get_service_action(service['id'])
                ServiceCard(service, service_action)

# --- Ejecución del Script ---
if __name__ == "__main__":
    main_app()