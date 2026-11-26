import api from './api'

const DB_NAME = 'techbok-offline-v1'
const STORE = 'outbox'
const CACHE_STORE = 'cache'
const DEVICE_KEY = 'techbok_device_id'
function deviceId() {
  let id = localStorage.getItem(DEVICE_KEY)
  if (!id) { id = crypto.randomUUID(); localStorage.setItem(DEVICE_KEY, id) }
  return id
}
function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 2)
    req.onupgradeneeded = () => { const db = req.result; if (!db.objectStoreNames.contains(STORE)) { const store=db.createObjectStore(STORE, {keyPath:'event_id'}); store.createIndex('created_at','created_at') } if (!db.objectStoreNames.contains(CACHE_STORE)) db.createObjectStore(CACHE_STORE) }
    req.onsuccess = () => resolve(req.result); req.onerror = () => reject(req.error)
  })
}
async function withStore(mode, action) {
  const db = await openDb()
  return new Promise((resolve, reject) => { const tx=db.transaction(STORE,mode); const store=tx.objectStore(STORE); const result=action(store); tx.oncomplete=()=>{db.close();resolve(result?.result)}; tx.onerror=()=>{db.close();reject(tx.error)} })
}
export async function saveOfflineSnapshot(snapshot) {
  const db=await openDb()
  return new Promise((resolve,reject)=>{const tx=db.transaction(CACHE_STORE,'readwrite');tx.objectStore(CACHE_STORE).put(snapshot,'staff_snapshot');tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>{db.close();reject(tx.error)}})
}
export async function getOfflineSnapshot() {
  const db=await openDb()
  return new Promise((resolve,reject)=>{const tx=db.transaction(CACHE_STORE,'readonly');const req=tx.objectStore(CACHE_STORE).get('staff_snapshot');req.onsuccess=()=>{db.close();resolve(req.result||null)};req.onerror=()=>{db.close();reject(req.error)}})
}
export async function clearOfflineSnapshot() {
  const db=await openDb()
  return new Promise((resolve,reject)=>{const tx=db.transaction(CACHE_STORE,'readwrite');tx.objectStore(CACHE_STORE).delete('staff_snapshot');tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>{db.close();reject(tx.error)}})
}

export async function queueOfflineOperation({entity_type, operation='upsert', payload, branch_id=null, user_id=null}) {
  if (!['student_draft','admission_enquiry','student_record','admission_application','enrollment_record','attendance_mark','assessment_answer','assessment_mark','finance_draft'].includes(entity_type)) throw new Error('Unsupported offline record type.')
  const event = {event_id:crypto.randomUUID(), device_id:deviceId(), queued_by:user_id, entity_type, operation, payload, branch_id, created_at:new Date().toISOString(), status:'pending'}
  await withStore('readwrite', store => store.put(event))
  window.dispatchEvent(new CustomEvent('techbok-outbox-changed'))
  return event
}
export async function listPendingOperations() {
  const db=await openDb()
  return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly');const req=tx.objectStore(STORE).getAll();req.onsuccess=()=>{db.close();resolve((req.result||[]).filter(x=>x.status==='pending').sort((a,b)=>a.created_at.localeCompare(b.created_at)))};req.onerror=()=>{db.close();reject(req.error)}})
}
export async function listAttentionOperations() {
  const db=await openDb()
  return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly');const req=tx.objectStore(STORE).getAll();req.onsuccess=()=>{db.close();resolve((req.result||[]).filter(x=>x.status==='needs_attention').sort((a,b)=>a.created_at.localeCompare(b.created_at)))};req.onerror=()=>{db.close();reject(req.error)}})
}
export async function pendingCount() { return (await listPendingOperations()).length }
export async function syncPendingOperations(userId=null) {
  if (!navigator.onLine) return {sent:0, pending:await pendingCount(), offline:true}
  const pendingEvents=await listPendingOperations()
  const events=pendingEvents.filter(e=>!e.queued_by || (userId && String(e.queued_by)===String(userId)))
  if (!events.length) return {sent:0,pending:0}
  let sent=0
  // Small batches make retries safer on unstable connections.
  for (let i=0;i<events.length;i+=25) {
    const batch=events.slice(i,i+25)
    const response=await api.post('sync/batch/', {device_id:deviceId(), events:batch.map(({status,...e})=>e)})
    const acknowledged=new Set(response.data.acknowledged||[])
    const rejected=response.data.rejected||[]
    await withStore('readwrite', store => {
      acknowledged.forEach(id=>store.delete(id))
      rejected.forEach(item=>{
        const req=store.get(item.event_id)
        req.onsuccess=()=>{if(req.result)store.put({...req.result,status:'needs_attention',error:item.reason||'The server rejected this record.'})}
      })
    })
    sent += acknowledged.size
  }
  window.dispatchEvent(new CustomEvent('techbok-outbox-changed'))
  return {sent,pending:await pendingCount(),rejected:events.length-sent}
}
export function startSyncListeners(onResult=()=>{}, userId=null) {
  const sync=async()=>{if(!navigator.onLine)return;try{onResult(await syncPendingOperations(userId))}catch(error){onResult({error:error.response?.data?.detail||'Sync will retry when the connection is available.',pending:await pendingCount()})}}
  window.addEventListener('online',sync)
  window.addEventListener('focus',sync)
  const timer=setInterval(sync,60000)
  sync()
  return ()=>{window.removeEventListener('online',sync);window.removeEventListener('focus',sync);clearInterval(timer)}
}
