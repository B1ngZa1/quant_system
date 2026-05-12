import { ref, computed } from 'vue'

export interface PriceAlert {
  id: string
  symbol: string
  condition: 'above' | 'below'
  price: number
  createdAt: number
  triggered: boolean
}

const alerts = ref<PriceAlert[]>([])
const STORAGE_KEY = 'quant_price_alerts'

function loadAlerts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) alerts.value = JSON.parse(raw)
  } catch { /* ignore */ }
}

function saveAlerts() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts.value))
}

loadAlerts()

export function useAlerts() {
  const activeAlerts = computed(() => alerts.value.filter(a => !a.triggered))
  const triggeredAlerts = computed(() => alerts.value.filter(a => a.triggered))

  function addAlert(symbol: string, condition: 'above' | 'below', price: number): PriceAlert {
    const alert: PriceAlert = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      symbol: symbol.toUpperCase(),
      condition,
      price,
      createdAt: Date.now(),
      triggered: false,
    }
    alerts.value.push(alert)
    saveAlerts()
    return alert
  }

  function removeAlert(id: string) {
    alerts.value = alerts.value.filter(a => a.id !== id)
    saveAlerts()
  }

  function checkAlerts(symbol: string, currentPrice: number): PriceAlert[] {
    const triggered: PriceAlert[] = []
    alerts.value.forEach(alert => {
      if (alert.triggered || alert.symbol !== symbol.toUpperCase()) return
      const hit =
        (alert.condition === 'above' && currentPrice >= alert.price) ||
        (alert.condition === 'below' && currentPrice <= alert.price)
      if (hit) {
        alert.triggered = true
        triggered.push(alert)
      }
    })
    if (triggered.length) saveAlerts()
    return triggered
  }

  function clearTriggered() {
    alerts.value = alerts.value.filter(a => !a.triggered)
    saveAlerts()
  }

  return { alerts, activeAlerts, triggeredAlerts, addAlert, removeAlert, checkAlerts, clearTriggered }
}
