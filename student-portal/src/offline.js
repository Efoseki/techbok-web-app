import api from './api'

const DB_NAME = 'techbok-offline-v1'
const STORE = 'outbox'
const DEVICE_KEY = 'techbok_device_id'
function deviceId() {
  let id = localStorage.getItem(DEVICE_KEY)
  if (!id) { id = crypto.randomUUID(); localStorage.setItem(DEVICE_KEY, id) }
  return id
}
function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => { const db = req.result; if (!db.objectStoreNames.contains(STORE)) { const store = db.createObjectStore(STORE, {keyPath:'event_id'}); store.createIndex('created_at','created_at') } }
    req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error)
  })
}
async function withStore(mode, action) {
  const db = await openDb()
  return new Promise((resolve, reject) => { const tx=db.transaction(STORE,mode); const store=tx.objectStore(STORE); const result=action(store); tx.oncomplete=()=>{db.close();resolve(result?.result)}; tx.onerror=()=>{db.close();reject(tx.error)} })
}
export async function queueOfflineOperation({entity_type, operation='upsert', payload, branch_id=null}) {
  if (!['student_draft','admission_enquiry','attendance_mark','assessment_answer','assessment_mark','finance_draft'].includes(entity_type)) throw new Error('Unsupported offline record type.')
  const event = {event_id:crypto.randomUUID(), device_id:deviceId(), entity_type, operation, payload, branch_id, created_at:new Date().toISOString(), status:'pending'}
  await withStore('readwrite', store => store.put(event))
  window.dispatchEvent(new CustomEvent('techbok-outbox-changed'))
  return event
}
export async function listPendingOperations() {
  const db=await openDb()
  return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly');const req=tx.objectStore(STORE).getAll();req.onsuccess=()=>{db.close();resolve((req.result||[]).sort((a,b)=>a.created_at.localeCompare(b.created_at)))};req.onerror=()=>{db.close();reject(req.error)}})
}
export async function pendingCount() { return (await listPendingOperations()).length }
export async function syncPendingOperations() {
  if (!navigator.onLine) return {sent:0, pending:await pendingCount(), offline:true}
  const events=await listPendingOperations()
  if (!events.length) return {sent:0,pending:0}
  let sent=0
  // Small batches make retries safer on unstable connections.
  for (let i=0;i<events.length;i+=25) {
    const batch=events.slice(i,i+25)
    const response=await api.post('sync/batch/', {device_id:deviceId(), events:batch.map(({status,...e})=>e)})
    const acknowledged=new Set(response.data.acknowledged||[])
    await withStore('readwrite', store => acknowledged.forEach(id=>store.delete(id)))
    sent += acknowledged.size
  }
  window.dispatchEvent(new CustomEvent('techbok-outbox-changed'))
  return {sent,pending:await pendingCount()}
}
export function startSyncListeners(onResult=()=>{}) {
  const sync=async()=>{if(!navigator.onLine)return;try{onResult(await syncPendingOperations())}catch(error){onResult({error:error.response?.data?.detail||'Sync will retry when the connection is available.',pending:await pendingCount()})}}
  window.addEventListener('online',sync)
  window.addEventListener('focus',sync)
  const timer=setInterval(sync,60000)
  sync()
  return ()=>{window.removeEventListener('online',sync);window.removeEventListener('focus',sync);clearInterval(timer)}
}
