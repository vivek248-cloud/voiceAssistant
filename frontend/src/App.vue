<script setup>
import { login, logout, authenticatedFetch } from './api'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Activity, AudioLines, Bot, ChevronDown, Cpu, Menu, Mic, MicOff, Plus, Send, ShieldCheck, Sparkles, Square, Volume2, VolumeX, Wifi, X, Cloud } from 'lucide-vue-next'

/* ---------- state ---------- */
const draft = ref('')
const busy = ref(false)
const mobileMenu = ref(false)
const privacyMode = ref('local')
const allowCloud = ref(false)
const providerStatus = ref('Local AI · Qwen')
const messages = ref([
  { role: 'assistant', content: 'Good day. JARVIS systems are online. How may I assist you?', provider: 'local', model: 'qwen2.5:1.5b-instruct' }
])
const chatBox = ref(null)
const clock = ref('')
const booting = ref(true)
const bootLines = ref([])
const lastLatency = ref(null)
const startedAt = Date.now()
const uptime = ref('00:00')
const cloudAllowed = computed(() => privacyMode.value !== 'local' && allowCloud.value)


/* ---------- authentication ---------- */
const isLoggedIn = ref(false)
const loginUsername = ref('')
const loginPassword = ref('')
const loginBusy = ref(false)
const loginError = ref('')

async function handleLogin() {
  if (loginBusy.value) return

  loginBusy.value = true
  loginError.value = ''

  try {
    await login(loginUsername.value.trim(), loginPassword.value)
    isLoggedIn.value = true
    loginPassword.value = ''
    loginError.value = ''
  } catch (error) {
    loginError.value = error.message || 'Login failed. Please try again.'
  } finally {
    loginBusy.value = false
  }
}

function handleLogout() {
  stopListening()
  stopSpeaking()
  logout()
  isLoggedIn.value = false
  loginPassword.value = ''
  loginError.value = ''
  draft.value = ''
  mobileMenu.value = false
  messages.value = [
    { role: 'assistant', content: 'Good day. JARVIS systems are online. How may I assist you?', provider: 'local', model: 'qwen2.5:1.5b-instruct' }
  ]
}

/* ---------- voice state ---------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition
const voiceSupported = !!SR && 'speechSynthesis' in window
const listening = ref(false)
const speaking = ref(false)
const interim = ref('')
const voiceNote = ref('')
const autoSpeak = ref(true)
const wakeWord = ref(false)
const showVoice = ref(false)
const voices = ref([])
const voiceName = ref(localStorage.getItem('jarvis.voice') || '')
const rate = ref(Number(localStorage.getItem('jarvis.rate')) || 1)
const pitch = ref(Number(localStorage.getItem('jarvis.pitch')) || 0.9)
const lang = ref(localStorage.getItem('jarvis.lang') || 'en-US')
const level = ref(0)

const orbState = computed(() =>
  busy.value ? 'thinking' : speaking.value ? 'speaking' : listening.value ? 'listening' : 'idle')
const orbLabel = computed(() => ({
  thinking: 'PROCESSING', speaking: 'SPEAKING', listening: wakeWord.value ? 'AWAITING "JARVIS"' : 'LISTENING', idle: 'STANDING BY'
}[orbState.value]))

let recognition = null
let micStream = null
let audioCtx = null
let rafId = 0
let pulseTimer = 0
let clockTimer = 0
let wantListening = false
let levelTimer = 0
let speakToken = 0

/* ---------- helpers ---------- */
const tier = () => (privacyMode.value === 'local' || !allowCloud.value)
  ? 'Local AI · Qwen'
  : privacyMode.value === 'cloud' ? 'Cloud AI · NVIDIA' : 'Hybrid AI · NVIDIA + Qwen'

function newChat() {
  stopSpeaking()
  messages.value = [{ role: 'assistant', content: 'New session initiated. What would you like to work on?', provider: 'local' }]
}
function changePrivacyMode() {
  if (privacyMode.value === 'local') allowCloud.value = false
  providerStatus.value = tier()
}
function usePrompt(p) { draft.value = p }
function providerLabel(p) {
  return p === 'nvidia' ? 'NVIDIA CLOUD' : p === 'local_fallback' ? 'LOCAL FALLBACK' : p === 'local' ? 'LOCAL QWEN' : 'AI SYSTEM'
}
function tick() {
  clock.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const s = Math.floor((Date.now() - startedAt) / 1000)
  uptime.value = `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
}
async function scrollDown() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

/* ---------- chat ---------- */
async function sendMessage() {
  const text = draft.value.trim()
  if (!text || busy.value) return
  providerStatus.value = (privacyMode.value !== 'local' && !allowCloud.value) ? 'Local only · Cloud permission is off' : tier()

  const history = messages.value.slice(-12).map(({ role, content }) => ({ role, content }))
  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  interim.value = ''
  busy.value = true
  stopSpeaking()
  scrollDown()
  const t0 = performance.now()
  try {
    const res = await authenticatedFetch('/api/chat/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: [...history, { role: 'user', content: text }],
        privacy_mode: privacyMode.value,
        allow_cloud: cloudAllowed.value
      })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Request failed')
    lastLatency.value = Math.round(performance.now() - t0)
    messages.value.push({ role: 'assistant', content: data.answer, provider: data.provider, model: data.model })
    providerStatus.value = data.provider === 'nvidia' ? 'NVIDIA Nemotron · Cloud'
      : data.provider === 'local_fallback' ? 'Qwen · Local fallback' : 'Qwen · Local'
    if (autoSpeak.value && voiceSupported) speak(data.answer)
  } catch (e) {
    if (e.message && (e.message.includes('session has expired') || e.message.includes('Please log in'))) {
      handleLogout()
      loginError.value = e.message
      return
    }
    messages.value.push({ role: 'assistant', content: `Connection issue: ${e.message}`, provider: 'error' })
    if (autoSpeak.value && voiceSupported) speak('I am having trouble reaching my core systems, sir.')
  } finally {
    busy.value = false
    scrollDown()
    if (wantListening && !speaking.value) resumeRecognition()
  }
}

/* ---------- text to speech ---------- */
function loadVoices() {
  const list = speechSynthesis.getVoices().filter(v => v.lang.startsWith('en'))
  voices.value = list
  if (!voiceName.value || !list.some(v => v.name === voiceName.value)) {
    const pref = ['Google UK English Male', 'Daniel', 'Microsoft Ryan', 'Microsoft George', 'Arthur', 'Oliver']
    const found = pref.map(p => list.find(v => v.name.includes(p))).find(Boolean) || list.find(v => v.lang === 'en-GB') || list[0]
    voiceName.value = found ? found.name : ''
  }
}
function cleanForSpeech(t) {
  return t
    .replace(/```[\s\S]*?```/g, ' code block omitted. ')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/[*_#>~]+/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/https?:\/\/\S+/g, 'link')
    .replace(/\s+/g, ' ')
    .trim()
}
function speak(text) {
  if (!voiceSupported) return
  const chunks = cleanForSpeech(text).match(/[^.!?\n]+[.!?]*/g) || []
  if (!chunks.length) return
  const token = ++speakToken
  speechSynthesis.cancel()
  pauseRecognition()
  speaking.value = true
  startPulse()
  const voice = voices.value.find(v => v.name === voiceName.value)
  const total = chunks.join(' ').length
  // Chrome drops speak() if it is called right after cancel(), so wait a moment
  setTimeout(() => {
    if (token !== speakToken) return
    chunks.forEach((c, i) => {
      const u = new SpeechSynthesisUtterance(c.trim())
      if (voice) u.voice = voice
      u.lang = voice ? voice.lang : 'en-GB'
      u.rate = rate.value
      u.pitch = pitch.value
      if (i === chunks.length - 1) {
        u.onend = () => { if (token === speakToken) finishSpeaking() }
        u.onerror = (e) => {
          if (token !== speakToken) return
          if (e.error === 'not-allowed') voiceNote.value = 'Browser blocked speech. Click anywhere on the page once, then try again.'
          finishSpeaking()
        }
      }
      speechSynthesis.speak(u)
    })
  }, 120)
  // watchdog: some voices never fire onend
  setTimeout(() => { if (token === speakToken && speaking.value) finishSpeaking() }, total * 120 / rate.value + 4000)
}
function finishSpeaking() {
  speaking.value = false
  stopPulse()
  if (wantListening) setTimeout(resumeRecognition, 400)
}
function stopSpeaking() {
  if (!voiceSupported) return
  speakToken++
  speechSynthesis.cancel()
  if (speaking.value) finishSpeaking()
}
function startPulse() {
  stopPulse()
  pulseTimer = setInterval(() => { level.value = 0.25 + Math.random() * 0.75 }, 110)
}
function stopPulse() { clearInterval(pulseTimer); if (!listening.value) level.value = 0 }
function previewVoice() { speak('All systems are online and operating at full capacity, sir.') }

/* ---------- speech recognition ---------- */
function buildRecognition() {
  const r = new SR()
  r.lang = lang.value
  r.continuous = true
  r.interimResults = true
  r.onstart = () => { voiceNote.value = 'Listening… speak now' }
  r.onspeechstart = () => { voiceNote.value = '' }
  r.onresult = (e) => {
    let live = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i]
      if (res.isFinal) handleVoice(res[0].transcript)
      else live += res[0].transcript
    }
    interim.value = live
    level.value = 0.3 + Math.random() * 0.7
    clearTimeout(levelTimer)
    levelTimer = setTimeout(() => { if (!speaking.value) level.value = 0 }, 400)
  }
  r.onerror = (e) => {
    const fatal = {
      'not-allowed': 'Microphone blocked. Click the lock icon in the address bar, allow Microphone, then press Voice on again.',
      'service-not-allowed': 'Speech service blocked. Use Chrome or Edge; Brave and Firefox do not support voice input.',
      'audio-capture': 'No microphone found. Check your system sound input settings.',
      'network': 'Speech service unreachable. Voice input needs internet and works in Chrome or Edge only (not Brave).',
      'language-not-supported': 'That listen language is not supported. Pick English (US) in Voice settings.'
    }[e.error]
    if (fatal) { stopListening(); voiceNote.value = fatal }
  }
  r.onend = () => { if (wantListening && !speaking.value) setTimeout(resumeRecognition, 250) }
  return r
}
function resumeRecognition() {
  if (!wantListening || speaking.value) return
  try { recognition && recognition.start() } catch { /* already started */ }
}
function pauseRecognition() {
  try { recognition && recognition.stop() } catch { /* not running */ }
}
function handleVoice(raw) {
  const text = raw.trim()
  if (!text) return
  if (/^(stop|be quiet|silence|shut up)\b/i.test(text)) { stopSpeaking(); return }
  if (wakeWord.value) {
    const m = text.match(/^(?:hey|ok|okay|hi)?[\s,]*(?:jarvis|jarvish|travis|service)\b[\s,.:!-]*(.*)$/i)
    if (!m) { voiceNote.value = `Ignored (no wake word): "${text.slice(0, 40)}"`; return }
    const cmd = m[1].trim()
    if (!cmd) { if (autoSpeak.value) speak('Yes, sir?'); return }
    voiceNote.value = ''
    draft.value = cmd
  } else {
    voiceNote.value = ''
    draft.value = text
  }
  sendMessage()
}
async function startLevelMeter() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const an = audioCtx.createAnalyser()
    an.fftSize = 256
    audioCtx.createMediaStreamSource(micStream).connect(an)
    const buf = new Uint8Array(an.frequencyBinCount)
    const loop = () => {
      an.getByteFrequencyData(buf)
      const avg = buf.reduce((a, b) => a + b, 0) / buf.length / 140
      if (!speaking.value) level.value = Math.min(1, avg * 1.8)
      rafId = requestAnimationFrame(loop)
    }
    loop()
  } catch { /* meter is optional */ }
}
function stopLevelMeter() {
  cancelAnimationFrame(rafId)
  micStream && micStream.getTracks().forEach(t => t.stop())
  audioCtx && audioCtx.close().catch(() => {})
  micStream = audioCtx = null
  if (!speaking.value) level.value = 0
}
async function startListening() {
  if (!voiceSupported) { voiceNote.value = 'Voice input is not supported in this browser. Open the app in Chrome or Edge (not Brave or Firefox).'; return }
  wantListening = true
  listening.value = true
  voiceNote.value = ''
  recognition = buildRecognition()
  resumeRecognition()
}
function stopListening() {
  wantListening = false
  listening.value = false
  interim.value = ''
  pauseRecognition()
  stopLevelMeter()
}
function toggleMic() { listening.value ? stopListening() : startListening() }
function onHotkey(e) {
  if (e.altKey && e.code === 'KeyJ') { e.preventDefault(); toggleMic() }
  if (e.key === 'Escape') stopSpeaking()
}

watch([voiceName, rate, pitch, lang], () => {
  localStorage.setItem('jarvis.voice', voiceName.value)
  localStorage.setItem('jarvis.rate', rate.value)
  localStorage.setItem('jarvis.pitch', pitch.value)
  localStorage.setItem('jarvis.lang', lang.value)
  if (listening.value) { stopListening(); startListening() }
})

/* ---------- lifecycle ---------- */
onMounted(() => {
  tick(); clockTimer = setInterval(tick, 1000)
  window.addEventListener('keydown', onHotkey)
  if (voiceSupported) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices }
  const seq = ['INITIALIZING CORE', 'LOADING LANGUAGE MODEL', 'CALIBRATING VOICE INTERFACE', 'PRIVACY GATE ARMED', 'ALL SYSTEMS NOMINAL']
  seq.forEach((l, i) => setTimeout(() => bootLines.value.push(l), 260 * (i + 1)))
  setTimeout(() => { booting.value = false }, 260 * seq.length + 600)
})
onBeforeUnmount(() => {
  clearInterval(clockTimer); stopPulse()
  window.removeEventListener('keydown', onHotkey)
  stopListening(); stopSpeaking()
})
</script>

<template>
  <div v-if="!isLoggedIn" class="login-screen">
    <div class="login-card">
      <div class="login-logo"><AudioLines :size="32" /></div>
      <div class="login-brand">J.A.R.V.I.S.</div>
      <div class="login-subtitle">PERSONAL INTELLIGENCE SYSTEM</div>

      <div class="login-heading">Welcome back</div>
      <p class="login-description">Authenticate to access your private AI workspace.</p>

      <form @submit.prevent="handleLogin">
        <label class="login-label" for="jarvis-username">ADMINISTRATOR USERNAME</label>
        <input
          id="jarvis-username"
          v-model="loginUsername"
          class="login-input"
          type="text"
          placeholder="Enter Django username"
          autocomplete="username"
          required
          autofocus
        />

        <label class="login-label" for="jarvis-password">PASSWORD</label>
        <input
          id="jarvis-password"
          v-model="loginPassword"
          class="login-input"
          type="password"
          placeholder="Enter your password"
          autocomplete="current-password"
          required
        />

        <div v-if="loginError" class="login-error" role="alert">{{ loginError }}</div>

        <button class="login-submit" type="submit" :disabled="loginBusy || !loginUsername.trim() || !loginPassword">
          {{ loginBusy ? 'AUTHENTICATING...' : 'ACCESS JARVIS' }}
        </button>
      </form>

      <div class="login-security"><ShieldCheck :size="14" /> Secure administrator authentication</div>
    </div>
  </div>

  <div v-else>
  <div class="shell" :class="`state-${orbState}`" :style="{ '--lvl': level }">
    <div class="hud-grid" aria-hidden="true"></div>
    <div class="scanline" aria-hidden="true"></div>

    <transition name="boot">
      <div v-if="booting" class="boot">
        <div class="boot-reactor"><AudioLines :size="30" /></div>
        <div class="boot-title">J.A.R.V.I.S.</div>
        <div class="boot-lines"><div v-for="l in bootLines" :key="l">&gt; {{ l }}</div></div>
      </div>
    </transition>

    <aside class="sidebar" :class="{ 'sidebar-open': mobileMenu }">
      <div class="brand">
        <div class="brand-mark"><AudioLines :size="22" /></div>
        <div><div class="brand-title">J.A.R.V.I.S.</div><div class="brand-sub">PERSONAL INTELLIGENCE</div></div>
        <button class="icon-button mobile-close" @click="mobileMenu = false"><X :size="18" /></button>
      </div>
      <button class="new-chat" @click="newChat"><Plus :size="17" /> New conversation</button>

      <div class="nav-label">SYSTEM</div>
      <div class="nav-item active"><Bot :size="17" /> Assistant <span class="nav-dot"></span></div>
      <div class="nav-item muted"><Activity :size="17" /> Activity monitor <span class="soon">SOON</span></div>
      <div class="nav-item muted"><ShieldCheck :size="17" /> Personal memory <span class="soon">SOON</span></div>

      <div class="nav-label tools-label">TELEMETRY</div>
      <div class="telemetry">
        <div><small>UPTIME</small><b>{{ uptime }}</b></div>
        <div><small>LAST REPLY</small><b>{{ lastLatency ? (lastLatency / 1000).toFixed(1) + 's' : '—' }}</b></div>
        <div><small>MESSAGES</small><b>{{ messages.length }}</b></div>
        <div><small>VOICE</small><b>{{ voiceSupported ? (listening ? 'LIVE' : 'READY') : 'N/A' }}</b></div>
      </div>

      <div class="nav-label tools-label">QUICK PROMPTS</div>
      <button class="prompt-link" @click="usePrompt('Help me plan my day with priorities and time blocks.')">Plan my day</button>
      <button class="prompt-link" @click="usePrompt('Explain this topic simply, then give me a practical example: ')">Explain a topic</button>
      <button class="prompt-link" @click="usePrompt('Help me calculate and compare these numbers: ')">Run a calculation</button>

      <div class="sidebar-bottom">
        <div class="profile"><div class="avatar">V</div><div><strong>Local operator</strong><small>Private workspace</small></div><ChevronDown :size="16" class="profile-chevron" /></div>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <button class="icon-button menu-button" @click="mobileMenu = !mobileMenu"><Menu :size="20" /></button>
        <div class="breadcrumb">Workspace <span>/</span> <b>Assistant</b></div>
        <div class="top-status"><span class="live-dot"></span> SYSTEM NOMINAL <span class="top-divider"></span><span class="time">{{ clock }}</span><button class="logout-button" type="button" @click="handleLogout">Logout</button></div>
      </header>

      <section class="content">
        <div class="hero">
          <div class="eyebrow"><span class="eyebrow-line"></span> PERSONAL AI INTERFACE <span class="eyebrow-line"></span></div>

          <button class="reactor-wrap" :class="`orb-${orbState}`" @click="toggleMic" :title="listening ? 'Mute microphone (Alt+J)' : 'Activate voice (Alt+J)'" aria-label="Toggle voice">
            <span class="ring ring-a"></span><span class="ring ring-b"></span><span class="ring ring-c"></span>
            <span class="ticks"></span>
            <span class="halo"></span>
            <span class="reactor"><span class="reactor-inner"><component :is="listening ? Mic : AudioLines" :size="35" /></span></span>
            <span class="bars" aria-hidden="true"><i v-for="n in 24" :key="n" :style="{ '--i': n }"></i></span>
          </button>

          <div class="orb-label">{{ orbLabel }}</div>
          <h1>At your service<span>.</span></h1>
          <p class="hero-copy">{{ listening && wakeWord ? 'Say “Jarvis” followed by your request.' : 'Intelligence at your fingertips. What shall we accomplish today?' }}</p>

          <div class="metrics">
            <div class="metric"><span class="metric-icon"><Cpu :size="15" /></span><div><small>ACTIVE MODEL</small><strong>{{ providerStatus }}</strong></div></div>
            <div class="metric"><span class="metric-icon"><ShieldCheck :size="15" /></span><div><small>PRIVACY DEFAULT</small><strong>Local processing</strong></div></div>
            <div class="metric"><span class="metric-icon"><Wifi :size="15" /></span><div><small>INTERFACE</small><strong>Local workspace</strong></div></div>
          </div>
        </div>

        <section class="chat-panel">
          <i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
          <div class="panel-heading"><div><span class="panel-led"></span><strong>Conversation</strong><small> · Secure model gateway</small></div><button class="clear-button" @click="newChat">Clear session</button></div>

          <div class="privacy-controls">
            <div class="privacy-heading"><ShieldCheck :size="16" /><div><strong>AI routing & privacy</strong><small>Local is the default. Cloud is opt-in.</small></div></div>
            <label class="mode-field">AI MODE
              <select v-model="privacyMode" @change="changePrivacyMode">
                <option value="local">Local · Qwen only</option>
                <option value="hybrid">Hybrid · NVIDIA + local fallback</option>
                <option value="cloud">Cloud · NVIDIA only</option>
              </select>
            </label>
            <label class="cloud-consent" :class="{ disabled: privacyMode === 'local' }">
              <input v-model="allowCloud" type="checkbox" :disabled="privacyMode === 'local'" @change="changePrivacyMode">
              <span><b>Allow cloud processing</b><small v-if="privacyMode === 'local'">Switch to Hybrid or Cloud to enable this.</small><small v-else>When enabled, your message and included history may be sent to NVIDIA.</small></span>
            </label>
            <div class="privacy-warning" v-if="privacyMode !== 'local' && !allowCloud"><ShieldCheck :size="14" /> Cloud permission is off. Requests will stay on your PC.</div>
            <div class="privacy-warning cloud-on" v-else-if="allowCloud"><Cloud :size="14" /> Cloud permission enabled. Avoid sending sensitive information.</div>
          </div>

          <div class="voice-bar">
            <button class="mic-btn" :class="{ on: listening }" :disabled="!voiceSupported" @click="toggleMic">
              <component :is="listening ? MicOff : Mic" :size="15" /> {{ listening ? 'Mute mic' : 'Voice on' }}
            </button>
            <button class="chip" :class="{ on: autoSpeak }" @click="autoSpeak = !autoSpeak; if (!autoSpeak) stopSpeaking()">
              <component :is="autoSpeak ? Volume2 : VolumeX" :size="14" /> Speak replies
            </button>
            <button class="chip" :class="{ on: wakeWord }" @click="wakeWord = !wakeWord">Wake word “Jarvis”</button>
            <button v-if="speaking" class="chip stop" @click="stopSpeaking"><Square :size="12" /> Stop</button>
            <button class="chip" @click="showVoice = !showVoice">Voice settings</button>
            <span class="voice-hint">Alt+J mic · Esc silence</span>
          </div>

          <div v-if="showVoice" class="voice-settings">
            <label>VOICE
              <select v-model="voiceName"><option v-for="v in voices" :key="v.name" :value="v.name">{{ v.name }} ({{ v.lang }})</option></select>
            </label>
            <label>LISTEN LANGUAGE
              <select v-model="lang"><option value="en-US">English (US)</option><option value="en-GB">English (UK)</option><option value="en-IN">English (India)</option><option value="ta-IN">Tamil</option><option value="hi-IN">Hindi</option></select>
            </label>
            <label>SPEED {{ rate.toFixed(2) }}<input type="range" min="0.7" max="1.4" step="0.05" v-model.number="rate"></label>
            <label>PITCH {{ pitch.toFixed(2) }}<input type="range" min="0.5" max="1.5" step="0.05" v-model.number="pitch"></label>
            <button class="chip on" @click="previewVoice">Test voice</button>
          </div>
          <div v-if="voiceNote" class="voice-note">{{ voiceNote }}</div>

          <div ref="chatBox" class="messages">
            <div v-for="(msg, i) in messages" :key="i" class="message-row" :class="msg.role">
              <div class="message-avatar"><AudioLines v-if="msg.role === 'assistant'" :size="16" /><span v-else>V</span></div>
              <div class="message-body">
                <div class="message-meta">{{ msg.role === 'assistant' ? 'JARVIS' : 'YOU' }} <span>· {{ msg.role === 'assistant' ? providerLabel(msg.provider) : 'OPERATOR' }}</span>
                  <button v-if="msg.role === 'assistant' && voiceSupported" class="replay" @click="speak(msg.content)" title="Read aloud"><Volume2 :size="12" /></button>
                </div>
                <div class="message-text">{{ msg.content }}</div>
                <div v-if="msg.model" class="model-stamp">{{ msg.model }}</div>
              </div>
            </div>
            <div v-if="busy" class="message-row assistant"><div class="message-avatar"><AudioLines :size="16" /></div><div class="message-body"><div class="message-meta">JARVIS <span>· PROCESSING</span></div><div class="typing"><i></i><i></i><i></i> <span>Thinking</span></div></div></div>
          </div>

          <div class="composer">
            <div class="composer-top"><Sparkles :size="14" /> <span>{{ interim ? 'Hearing: ' + interim : 'Ask JARVIS anything' }}</span><span class="composer-hint">ENTER TO SEND</span></div>
            <form @submit.prevent="sendMessage">
              <textarea v-model="draft" rows="2" placeholder="Type a message, or turn on voice and say “Jarvis, …”" @keydown.enter.exact.prevent="sendMessage"></textarea>
              <div class="composer-bottom">
                <div class="compose-note"><span class="tiny-lock">⌑</span> API key stays on backend · {{ cloudAllowed ? 'Cloud permitted' : 'Local only' }}</div>
                <button class="send-button" :disabled="busy || !draft.trim()" type="submit"><span>{{ busy ? 'Working' : 'Send' }}</span><Send :size="15" /></button>
              </div>
            </form>
          </div>
        </section>
        <footer><span>J.A.R.V.I.S. INTERFACE <b>v0.3</b></span><span><span class="live-dot"></span> ALL SYSTEMS STANDING BY</span></footer>
      </section>
    </main>
    <div v-if="mobileMenu" class="scrim" @click="mobileMenu = false"></div>
  </div>
  </div>
</template>


<style scoped>
.login-screen {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
  background: #080d16;
  color: #eaf5ff;
}

.login-card {
  width: 100%;
  max-width: 420px;
  box-sizing: border-box;
  padding: 42px 36px;
  border: 1px solid rgba(90, 180, 255, 0.2);
  border-radius: 18px;
  background: #101927;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.45);
}

.login-logo {
  width: 62px;
  height: 62px;
  margin: 0 auto 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #65c8ff;
  border: 1px solid rgba(101, 200, 255, 0.4);
  border-radius: 16px;
}

.login-brand {
  text-align: center;
  color: #eaf5ff;
  font-size: 25px;
  font-weight: 700;
  letter-spacing: 5px;
}

.login-subtitle {
  text-align: center;
  color: #6f91aa;
  font-size: 9px;
  letter-spacing: 2px;
  margin-top: 8px;
}

.login-heading {
  color: #f0f6ff;
  font-size: 23px;
  font-weight: 600;
  margin-top: 38px;
}

.login-description {
  color: #91a4b9;
  font-size: 13px;
  margin: 8px 0 28px;
}

.login-label {
  display: block;
  color: #91b5ce;
  font-size: 10px;
  letter-spacing: 1.5px;
  margin: 20px 0 9px;
}

.login-input {
  box-sizing: border-box;
  width: 100%;
  padding: 14px;
  border: 1px solid #293e52;
  border-radius: 8px;
  background: #0a1320;
  color: #fff;
  outline: none;
}

.login-input:focus {
  border-color: #55baff;
  box-shadow: 0 0 0 3px rgba(85, 186, 255, 0.1);
}

.login-submit {
  width: 100%;
  margin-top: 26px;
  padding: 15px;
  border: 0;
  border-radius: 8px;
  background: #168bd1;
  color: #fff;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
}

.login-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-error {
  color: #ff8585;
  font-size: 13px;
  margin-top: 15px;
}

.login-security {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 25px;
  color: #7195aa;
  font-size: 11px;
}

.logout-button {
  margin-left: 12px;
  padding: 7px 11px;
  border: 1px solid rgba(120, 170, 205, 0.3);
  border-radius: 7px;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.logout-button:hover {
  border-color: #65c8ff;
  color: #65c8ff;
}

@media (max-width: 480px) {
  .login-card {
    padding: 32px 22px;
  }
  .logout-button {
    margin-left: 6px;
    padding: 6px 8px;
  }
}
</style>
