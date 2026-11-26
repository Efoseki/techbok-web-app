import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

createApp(App).mount('#app')

// Vite development must not be controlled by an older production service worker.
// Remove any previously installed worker and its stale shell cache while developing.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    if (import.meta.env.DEV) {
      const registrations = await navigator.serviceWorker.getRegistrations()
      await Promise.all(registrations.map((registration) => registration.unregister()))

      if ('caches' in window) {
        const cacheNames = await caches.keys()
        await Promise.all(
          cacheNames
            .filter((name) => name.startsWith('techbok-shell-'))
            .map((name) => caches.delete(name)),
        )
      }
      return
    }

    if (import.meta.env.PROD) {
      navigator.serviceWorker.register('/sw.js').catch((error) => {
        console.error('Student portal service worker registration failed:', error)
      })
    }
  })
}
