<script setup>
import { computed, nextTick, ref } from 'vue'
import { Activity, AudioLines, Bot, ChevronDown, Cpu, Menu, Plus, Send, ShieldCheck, Sparkles, Wifi, X, Cloud, Monitor } from 'lucide-vue-next'

const draft = ref('')
const busy = ref(false)
const mobileMenu = ref(false)
const privacyMode = ref('local')
const allowCloud = ref(false)
const providerStatus = ref('Local AI · Qwen')
const messages = ref([
  { role: 'assistant', content: "Good day. JARVIS systems are online. How may I assist you?", provider: 'local', model: 'qwen2.5:1.5b-instruct' }
])
const chatBox = ref(null)
const clock = ref(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
const cloudAllowed = computed(() => privacyMode.value !== 'local' && allowCloud.value)

function newChat() {
  messages.value = [{ role: 'assistant', content: 'New session initiated. What would you like to work on?', provider: 'local' }]
}
function changePrivacyMode() {
  if (privacyMode.value === 'local') allowCloud.value = false
  providerStatus.value = privacyMode.value === 'local' || !allowCloud.value
    ? 'Local AI · Qwen'
    : privacyMode.value === 'cloud' ? 'Cloud AI · NVIDIA' : 'Hybrid AI · NVIDIA + Qwen'
}
async function sendMessage() {
  const text = draft.value.trim()
  if (!text || busy.value) return

  if (privacyMode.value !== 'local' && !allowCloud.value) {
    providerStatus.value = 'Local only · Cloud permission is off'
  } else {
    providerStatus.value = privacyMode.value === 'local'
      ? 'Local AI · Qwen'
      : privacyMode.value === 'cloud' ? 'Cloud AI · NVIDIA' : 'Hybrid AI · NVIDIA + Qwen'
  }

  const history = messages.value.slice(-12).map(({ role, content }) => ({ role, content }))
  messages.value.push({ role: 'user', content: text })
  draft.value = ''
  busy.value = true
  await nextTick()
  try {
    const res = await fetch('http://127.0.0.1:8000/api/chat/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        history,
        privacy_mode: privacyMode.value,
        allow_cloud: cloudAllowed.value
      })
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Request failed')
    messages.value.push({
      role: 'assistant',
      content: data.answer,
      provider: data.provider,
      model: data.model
    })
    providerStatus.value = data.provider === 'nvidia'
      ? 'NVIDIA Nemotron · Cloud'
      : data.provider === 'local_fallback'
        ? 'Qwen · Local fallback'
        : 'Qwen · Local'
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `Connection issue: ${e.message}`, provider: 'error' })
  } finally {
    busy.value = false
    await nextTick()
    if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}
function usePrompt(prompt) {
  draft.value = prompt
}
function providerLabel(provider) {
  if (provider === 'nvidia') return 'NVIDIA CLOUD'
  if (provider === 'local_fallback') return 'LOCAL FALLBACK'
  if (provider === 'local') return 'LOCAL QWEN'
  return 'AI SYSTEM'
}
</script>

<template>
  <div class="shell">
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
        <div class="top-status"><span class="live-dot"></span> SYSTEM NOMINAL <span class="top-divider"></span><span class="time">{{ clock }}</span></div>
      </header>

      <section class="content">
        <div class="hero">
          <div class="eyebrow"><span class="eyebrow-line"></span> PERSONAL AI INTERFACE <span class="eyebrow-line"></span></div>
          <div class="reactor-wrap">
            <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><div class="orbit orbit-three"></div>
            <div class="reactor"><div class="reactor-inner"><AudioLines :size="35" /></div></div>
          </div>
          <h1>At your service<span>.</span></h1>
          <p class="hero-copy">Intelligence at your fingertips. What shall we accomplish today?</p>
          <div class="metrics">
            <div class="metric"><span class="metric-icon"><Cpu :size="15" /></span><div><small>ACTIVE MODEL</small><strong>{{ providerStatus }}</strong></div></div>
            <div class="metric"><span class="metric-icon"><ShieldCheck :size="15" /></span><div><small>PRIVACY DEFAULT</small><strong>Local processing</strong></div></div>
            <div class="metric"><span class="metric-icon"><Wifi :size="15" /></span><div><small>INTERFACE</small><strong>Local workspace</strong></div></div>
          </div>
        </div>

        <section class="chat-panel">
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
            <div class="privacy-warning" v-if="privacyMode !== 'local' && !allowCloud"> <ShieldCheck :size="14" /> Cloud permission is off. Requests will stay on your PC.</div>
            <div class="privacy-warning cloud-on" v-else-if="allowCloud"><Cloud :size="14" /> Cloud permission enabled. Avoid sending sensitive information.</div>
          </div>
          <div ref="chatBox" class="messages">
            <div v-for="(msg, i) in messages" :key="i" class="message-row" :class="msg.role">
              <div class="message-avatar"><AudioLines v-if="msg.role === 'assistant'" :size="16" /><span v-else>V</span></div>
              <div class="message-body"><div class="message-meta">{{ msg.role === 'assistant' ? 'JARVIS' : 'YOU' }} <span>· {{ msg.role === 'assistant' ? providerLabel(msg.provider) : 'OPERATOR' }}</span></div><div class="message-text">{{ msg.content }}</div><div v-if="msg.model" class="model-stamp">{{ msg.model }}</div></div>
            </div>
            <div v-if="busy" class="message-row assistant"><div class="message-avatar"><AudioLines :size="16" /></div><div class="message-body"><div class="message-meta">JARVIS <span>· PROCESSING</span></div><div class="typing"><i></i><i></i><i></i> <span>Thinking</span></div></div></div>
          </div>
          <div class="composer">
            <div class="composer-top"><Sparkles :size="14" /> <span>Ask JARVIS anything</span><span class="composer-hint">ENTER TO SEND</span></div>
            <form @submit.prevent="sendMessage">
              <textarea v-model="draft" rows="2" placeholder="Type a message or ask a question..." @keydown.enter.exact.prevent="sendMessage"></textarea>
              <div class="composer-bottom"><div class="compose-note"><span class="tiny-lock">⌑</span> API key stays on backend · {{ cloudAllowed ? 'Cloud permitted' : 'Local only' }}</div><button class="send-button" :disabled="busy || !draft.trim()" type="submit"><span>{{ busy ? 'Working' : 'Send' }}</span><Send :size="15" /></button></div>
            </form>
          </div>
        </section>
        <footer><span>J.A.R.V.I.S. INTERFACE <b>v0.2</b></span><span><span class="live-dot"></span> ALL SYSTEMS STANDING BY</span></footer>
      </section>
    </main>
    <div v-if="mobileMenu" class="scrim" @click="mobileMenu = false"></div>
  </div>
</template>
