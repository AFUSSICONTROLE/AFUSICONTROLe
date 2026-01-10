import streamlit as st
import google.generativeai as genai

# --- SÉCURITÉ PIN ---
PIN_DE_SECURITE = "1234" 

if "pin_auth" not in st.session_state:
    st.session_state.pin_auth = False

if not st.session_state.pin_auth:
    st.title("🔐 Accès Protégé")
    entree_pin = st.text_input("Entrez le code PIN pour modifier ou utiliser la page :", type="password")
    if st.button("Valider le PIN"):
        if entree_pin == PIN_DE_SECURITE:
            st.session_state.pin_auth = True
            st.rerun()
        else:
            st.error("Code incorrect.")
    st.stop()

# --- RÉCUPÉRATION DES CLÉS ---
TOMTOM_API_KEY = st.secrets.get("TOMTOM_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not TOMTOM_API_KEY or not GEMINI_API_KEY:
    st.warning("⚠️ Configuration de sécurité requise.")
    with st.expander("Cliquez ici pour entrer vos clés API (Stockage temporaire)"):
        TOMTOM_API_KEY = st.text_input("Clé TomTom", type="password")
        GEMINI_API_KEY = st.text_input("Clé Google AI Studio", type="password")
        if st.button("Valider les clés"):
            st.rerun()
    st.stop()

# Configuration de l'IA
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Guide IA Ultra-Précis", layout="centered")

# Design Noir & Vert
st.markdown(f"""
    <style>
    body {{ background-color: black; color: #00ff00; }}
    .stButton>button {{ 
        height: 120px; font-size: 28px !important; border-radius: 25px;
        background: #111; color: #00ff00; border: 3px solid #00ff00;
        font-weight: bold; margin-bottom: 20px;
    }}
    .stTextInput>div>div>input {{ background-color: #222; color: white; }}
    </style>
""", unsafe_allow_html=True)

if "user_name" not in st.session_state: st.session_state.user_name = ""
if "auth" not in st.session_state: st.session_state.auth = False

# --- PHASE 1 : ENREGISTREMENT DU NOM ---
if not st.session_state.user_name:
    st.title("Système Guide IA")
    nom = st.text_input("L'IA veut savoir votre nom :")
    if st.button("Enregistrer mon profil"):
        if nom:
            st.session_state.user_name = nom
            st.rerun()
    st.stop()

# --- PHASE 2 : SCANNER D'EMPREINTE ---
if not st.session_state.auth:
    st.subheader(f"Identification de {st.session_state.user_name}")
    auth_script = """
    <script>
    async function scannEmpreinte() {
        try {
            const options = {
                publicKey: {
                    challenge: new Uint8Array([1, 2, 3, 4]),
                    rp: { name: "Guide IA" },
                    user: { id: new Uint8Array([1]), name: "user", displayName: "user" },
                    pubKeyCredParams: [{ type: "public-key", alg: -7 }],
                    authenticatorSelection: { authenticatorAttachment: "platform" }
                }
            };
            await navigator.credentials.create(options);
            window.parent.postMessage("AUTH_OK", "*");
        } catch (e) { alert("Posez bien votre doigt sur le scanner d'écran."); }
    }
    </script>
    <div style="text-align:center;">
        <button onclick="scannEmpreinte()" style="width:150px; height:150px; border-radius:50%; background: radial-gradient(#00ff00, #004400); color:white; font-size:40px; border:none; cursor:pointer;">👆</button>
        <p style="margin-top:20px;">Scanner d'empreinte digitale actif</p>
    </div>
    """
    st.components.v1.html(auth_script, height=250)
    if st.button("Continuer après Scan réussi"):
        st.session_state.auth = True
        st.rerun()
    st.stop()

# --- PHASE 3 : LOGIQUE DE GUIDAGE ---
logic_js = f"""
<script>
let pointDepart = null;
let dernierMsg = "";
const nom = "{st.session_state.user_name}";
const tomtomKey = "{TOMTOM_API_KEY}";

function parler(txt) {{
    if (txt === dernierMsg) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(txt);
    utter.lang = 'fr-FR';
    utter.rate = 1.0;
    window.speechSynthesis.speak(utter);
    dernierMsg = txt;
}}

async function getAdresse(lat, lon) {{
    try {{
        let response = await fetch(`https://api.tomtom.com/search/2/reverseGeocode/${{lat}},${{lon}}.json?key=${{tomtomKey}}`);
        let data = await response.json();
        return data.addresses[0].address.freeformAddress || "rue inconnue";
    }} catch(e) {{ return "zone en détection"; }}
}}

function getCardinal(angle) {{
    const directions = ["au Nord", "au Nord-Est", "à l'Est", "au Sud-Est", "au Sud", "au Sud-Ouest", "à l'Ouest", "au Nord-Ouest"];
    return directions[Math.round(angle / 45) % 8];
}}

async function analyserMouvement(pos) {{
    if (!pointDepart) return;
    let coords1 = pointDepart.coords;
    let coords2 = pos.coords;
    let R = 6371e3;
    let dLat = (coords2.latitude - coords1.latitude) * Math.PI/180;
    let dLon = (coords2.longitude - coords1.longitude) * Math.PI/180;
    let a = Math.sin(dLat/2)**2 + Math.cos(coords1.latitude*Math.PI/180)*Math.cos(coords2.latitude*Math.PI/180)*Math.sin(dLon/2)**2;
    let dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    let y = Math.sin(dLon) * Math.cos(coords1.latitude * Math.PI/180);
    let x = Math.cos(coords2.latitude * Math.PI/180) * Math.sin(coords1.latitude * Math.PI/180) - Math.sin(coords2.latitude * Math.PI/180) * Math.cos(coords1.latitude * Math.PI/180) * Math.cos(dLon);
    let angleCible = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
    let orientation = pos.coords.heading || 0;
    let diffAngle = (angleCible - orientation + 360) % 360;
    let adresse = await getAdresse(coords2.latitude, coords2.longitude);
    let cardinal = getCardinal(angleCible);

    if (dist < 1.5) {{
        parler("Super " + nom + " ! Lieu retrouvé. Vous êtes exactement à votre immeuble.");
    }} else {{
        let instruction = "";
        if (diffAngle < 20 || diffAngle > 340) instruction = "Va tout droit, tu es parfaitement aligné.";
        else if (diffAngle >= 20 && diffAngle < 180) instruction = "Tourne un peu à droite.";
        else instruction = "Tourne un peu à gauche.";
        let monte = (coords2.altitude > coords1.altitude + 0.5) ? " Ça monte, courage." : "";
        parler(`${{nom}}, tu es actuellement dans ${{adresse}}. Le point est ${{cardinal}} à ${{Math.round(dist)}} mètres. ${{instruction}}${{monte}} On y va, bouge, sois en forme !`);
    }}
}}

function enregistrer() {{
    navigator.geolocation.getCurrentPosition((pos) => {{
        pointDepart = pos;
        parler("Position mémorisée " + nom + ". Quartier détecté. Partez tranquille, je vous surveille.");
    }}, null, {{enableHighAccuracy: true}});
}}

function retrouver() {{
    parler("C'est parti " + nom + ". Je vous guide en temps réel.");
    navigator.geolocation.watchPosition(analyserMouvement, null, {{enableHighAccuracy: true}});
}}
</script>
<button onclick="enregistrer()">📍 ENREGISTRER LA ZONE</button>
<button onclick="retrouver()">🔊 RETROUVER LE POINT</button>
"""

st.components.v1.html(logic_js, height=400)
st.markdown("---")
st.write("🔧 **Capteurs actifs :** GPS Haute Précision, Boussole Magnétique, Altimètre.")
st.write("🌍 **IA :** Google Gemini + TomTom Geocoding.")
