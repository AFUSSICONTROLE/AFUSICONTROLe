/**
 * AFUSSI LEMONFA PRO - Système d'Intelligence Supérieure
 * Configuré avec la Clé de Sang du Maître
 */

// --- 1. CONFIGURATION ET ÉTATS ---
let db;
let estIdentifie = false;
let modeGarde = false;
let pointTresor = null;
const PIN_MAITRE = "2026"; 

// RÉCUPÉRATION SÉCURISÉE DES CLÉS (LocalStorage pour éviter l'affichage public)
let GEMINI_API_KEY = localStorage.getItem('AFUSSI_GEMINI') || "AIzaSyCTgsjZJilsudlmXK9Nu7GKup0_N9Wra70"; 
let OPENAI_API_KEY = localStorage.getItem('AFUSSI_OPENAI') || "VOTRE_CLE_OPENAI";
let ELEVENLABS_API_KEY = localStorage.getItem('AFUSSI_ELEVEN') || "VOTRE_CLE_ELEVENLABS";
let VOICE_ID = localStorage.getItem('AFUSSI_VOICE') || "EX: Voice_Béninoise_Prestigieuse";

// Initialisation Microphone avec gestion d'erreur mobile
let recognition;
try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.lang = 'fr-FR';
    recognition.interimResults = false;
} catch (e) {
    console.error("Le navigateur ne supporte pas la reconnaissance vocale.");
}

// --- 2. MÉMOIRE INTERNE (IndexedDB) ---
const req = indexedDB.open("AfussiSupremeCore", 3);
req.onupgradeneeded = e => {
    db = e.target.result;
    if (!db.objectStoreNames.contains("memoire")) db.createObjectStore("memoire", { keyPath: "id", autoIncrement: true });
    if (!db.objectStoreNames.contains("positions")) db.createObjectStore("positions", { keyPath: "nom" });
};
req.onsuccess = e => {
    db = e.target.result;
    // Tenter de récupérer le trésor au démarrage
    const tx = db.transaction("positions", "readonly");
    const store = tx.objectStore("positions");
    const getPos = store.get("tresor");
    getPos.onsuccess = () => { if(getPos.result) pointTresor = getPos.result.coords; };
};

// --- 3. SÉCURITÉ ET AUTHENTIFICATION ---
// Cette fonction est appelée par le bouton du HTML
window.verifierIdentite = function() {
    const input = document.getElementById('pin-code').value;
    if (input === PIN_MAITRE) {
        estIdentifie = true;
        // On demande la clé Gemini si elle n'est pas déjà là (sécurité sup)
        if (!GEMINI_API_KEY || GEMINI_API_KEY.includes("VOTRE")) {
             const key = prompt("Maître, entrez votre clé API Gemini :");
             if(key) { localStorage.setItem('AFUSSI_GEMINI', key); GEMINI_API_KEY = key; }
        }
        
        document.getElementById('ai-orb').classList.add('ai-active');
        parler("Identité confirmée. Mon sang, mon Maître. Je suis éveillé.");
        surveillerBatterie();
    } else {
        parler("Alerte ! Tentative d'intrusion.");
    }
};

// --- 4. RÉFLEXION SUPÉRIEURE (GEMINI) ---
async function reflechir(message) {
    if (!navigator.onLine) return "Mode Hors-ligne : Je surveille les satellites.";
    
    try {
        const resp = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                contents: [{ parts: [{ text: `Tu es Afussi Lemonfa, IA béninoise supérieure. Réponds avec loyauté et humour à : ${message}` }] }]
            })
        });
        const data = await resp.json();
        return data.candidates[0].content.parts[0].text;
    } catch (e) {
        return "Analyse locale : Je vous écoute Maître (Erreur API).";
    }
}

// --- 5. VOIX ---
window.parler = async function(texte) {
    const consoleDiv = document.getElementById('log-console');
    if(consoleDiv) {
        consoleDiv.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${texte}</div>`;
        document.getElementById('chat-window').scrollTop = 9999;
    }

    if (navigator.onLine && !ELEVENLABS_API_KEY.includes("VOTRE")) {
        try {
            const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY },
                body: JSON.stringify({ text: texte, model_id: "eleven_multilingual_v2" })
            });
            if (response.ok) {
                const audioBlob = await response.blob();
                new Audio(URL.createObjectURL(audioBlob)).play();
                return;
            }
        } catch (e) {}
    }

    const utter = new SpeechSynthesisUtterance(texte);
    utter.lang = 'fr-FR'; utter.pitch = 0.9;
    window.speechSynthesis.speak(utter);
};

// --- 6. SENTINELLE, GPS & TRÉSOR ---
window.toggleModeGarde = function() {
    if (!estIdentifie) return parler("Accès bloqué.");
    modeGarde = !modeGarde;
    const btn = document.getElementById('btn-mode');
    if (modeGarde) {
        try {
            recognition.start();
            btn.innerText = "SENS DE DÉFENSE ACTIF";
            btn.classList.replace('bg-yellow-600', 'bg-red-600');
            parler("J'écoute l'environnement.");
        } catch(e) { parler("Erreur micro : Autorisez l'accès."); }
    } else {
        recognition.stop();
        btn.innerText = "ACTIVER SENTINELLE";
        btn.classList.replace('bg-red-600', 'bg-yellow-600');
        parler("Repos.");
    }
};

if(recognition) {
    recognition.onresult = async (e) => {
        const msg = e.results[e.results.length - 1][0].transcript.toLowerCase();
        if (msg.includes("voleur") || msg.includes("bagarre") || (msg.includes("afussi"))) {
            const rep = await reflechir(msg);
            parler(rep);
        }
    };
}

window.marquerZoneTresor = function() {
    if (!estIdentifie) return;
    navigator.geolocation.getCurrentPosition(pos => {
        pointTresor = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        const tx = db.transaction("positions", "readwrite");
        tx.objectStore("positions").put({ nom: "tresor", coords: pointTresor });
        parler("Zone marquée. Trésor sécurisé sous votre position.");
    }, err => parler("GPS indisponible. Activez la localisation."));
};

window.lancerTresor = function() {
    if (!estIdentifie || !pointTresor) return parler("Marquez d'abord une zone.");
    let secondes = (prompt("Minutes de recherche ?", "5") || 5) * 60;
    parler("Chasse lancée. Approchez-vous de la cible.");
    const chrono = setInterval(() => {
        secondes--;
        navigator.geolocation.getCurrentPosition(pos => {
            let d = Math.sqrt(Math.pow(pos.coords.latitude - pointTresor.lat, 2) + Math.pow(pos.coords.longitude - pointTresor.lng, 2)) * 111320;
            if (d < 5) { 
                clearInterval(chrono); 
                parler("Victoire ! Vous êtes sur le trésor !"); 
                navigator.vibrate([200, 100, 200]); 
            }
        });
        if (secondes <= 0) { clearInterval(chrono); parler("Temps écoulé, le trésor a disparu."); }
    }, 2000);
};

function surveillerBatterie() {
    if(navigator.getBattery) {
        navigator.getBattery().then(b => {
            const check = () => {
                document.getElementById('batt-status').innerText = `🔋 Batterie: ${Math.round(b.level * 100)}%`;
                if (b.level < 0.15) parler("Énergie critique, Maître.");
            };
            b.onlevelchange = check; check();
        });
    }
}
