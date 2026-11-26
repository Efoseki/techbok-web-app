<script setup>
import { computed, onMounted, ref } from 'vue'
import { BookOpen, Building2, GraduationCap, LayoutDashboard, LogOut, Search, ShieldCheck, Users, ClipboardList, UserPlus, Layers } from 'lucide-vue-next'
import api from './api'
import techbokLogo from './assets/techbok-logo.png'
import { pendingCount, startSyncListeners, queueOfflineOperation, saveOfflineSnapshot, getOfflineSnapshot, clearOfflineSnapshot, listAttentionOperations } from './offline'

const username=ref(''); const password=ref(''); const access=ref(localStorage.getItem('techbok_access')||'')
const error=ref(''); const loading=ref(false); const me=ref(null); const branches=ref([]); const courses=ref([])
const students=ref([]); const admissions=ref([]); const enrollments=ref([])
const search=ref(''); const activeTab=ref('Overview'); const online=ref(navigator.onLine); const pending=ref(0)
const syncMessage=ref(''); const attentionItems=ref([]); const draftTitle=ref(''); const draftNote=ref(''); let stopSync=null
const studentForm=ref({branch:'',first_name:'',middle_name:'',last_name:'',email:'',phone:'',date_of_birth:'',gender:'',address:'',guardian_name:'',guardian_phone:'',status:'active'})
const admissionForm=ref({branch:'',course:'',intake:'',first_name:'',middle_name:'',last_name:'',email:'',phone:'',date_of_birth:'',gender:'',address:'',guardian_name:'',guardian_phone:''})
const enrollmentForm=ref({student:'',branch:'',course:'',cohort:'',start_date:'',expected_end_date:'',tuition_fee:'0',other_fees:'0'})
const recordBusy=ref(false); const recordMessage=ref(''); const editingStudentId=ref(null)
const isLoggedIn=computed(()=>Boolean(access.value))
const filteredCourses=computed(()=>courses.value.filter(c=>(c.name+' '+c.code).toLowerCase().includes(search.value.toLowerCase())))
const filteredStudents=computed(()=>students.value.filter(s=>(s.student_number+' '+s.full_name+' '+s.email+' '+s.phone).toLowerCase().includes(search.value.toLowerCase())))
const filteredAdmissions=computed(()=>admissions.value.filter(a=>(a.application_number+' '+a.applicant_name+' '+a.course_name).toLowerCase().includes(search.value.toLowerCase())))
const filteredEnrollments=computed(()=>enrollments.value.filter(e=>(e.enrollment_number+' '+e.student_name+' '+e.course_name).toLowerCase().includes(search.value.toLowerCase())))
async function refreshPending(){try{pending.value=await pendingCount();attentionItems.value=await listAttentionOperations()}catch{pending.value=0;attentionItems.value=[]}}
async function saveOfflineDraft(){if(!draftTitle.value.trim()||!draftNote.value.trim()){syncMessage.value='Enter a title and note before saving.';return}try{await queueOfflineOperation({entity_type:'student_draft',operation:'upsert',payload:{title:draftTitle.value.trim(),note:draftNote.value.trim(),kind:'foundation_demo'},user_id:me.value?.id});draftTitle.value='';draftNote.value='';syncMessage.value='Saved on this device. It will sync when the server is reachable.';await refreshPending()}catch(e){syncMessage.value=e.message||'Could not save this offline draft.'}}
async function loadData(){
 loading.value=true;error.value=''
 try{
  const [u,b,c,st,ad,en]=await Promise.all([api.get('auth/me/'),api.get('branches/'),api.get('courses/'),api.get('students/'),api.get('admissions/'),api.get('enrollments/')])
  me.value=u.data;branches.value=b.data.results||b.data;courses.value=c.data.results||c.data
  students.value=st.data.results||st.data;admissions.value=ad.data.results||ad.data;enrollments.value=en.data.results||en.data
  if(!studentForm.value.branch&&branches.value.length)studentForm.value.branch=String(branches.value[0].id)
  if(!admissionForm.value.branch&&branches.value.length)admissionForm.value.branch=String(branches.value[0].id)
  if(!admissionForm.value.course&&courses.value.length)admissionForm.value.course=String(courses.value.find(x=>x.status==='active')?.id||courses.value[0].id)
  await saveOfflineSnapshot({me:me.value,branches:branches.value,courses:courses.value,students:students.value,admissions:admissions.value,enrollments:enrollments.value})
 }catch(e){
  if(e.response?.status===401){error.value='Your session has expired. Please sign in again.';logout(false)}
  else if(!e.response||!navigator.onLine){
   const snapshot=await getOfflineSnapshot().catch(()=>null)
   if(snapshot){me.value=snapshot.me||null;branches.value=snapshot.branches||[];courses.value=snapshot.courses||[];students.value=snapshot.students||[];admissions.value=snapshot.admissions||[];enrollments.value=snapshot.enrollments||[];if(!studentForm.value.branch&&branches.value.length)studentForm.value.branch=String(branches.value[0].id);if(!admissionForm.value.branch&&branches.value.length)admissionForm.value.branch=String(branches.value[0].id);if(!admissionForm.value.course&&courses.value.length)admissionForm.value.course=String(courses.value.find(x=>x.status==='active')?.id||courses.value[0].id);error.value='Offline mode: showing the last synchronised records. New records will be queued on this device.'}
   else error.value='Cannot reach the server and no offline snapshot is available. Connect and sign in once to prepare this device for offline use.'
  }else error.value=e.response?.data?.detail||'The server returned an error while loading the staff workspace. Check that the latest migrations have been applied.'
 }
 finally{loading.value=false}
}
async function login(){loading.value=true;error.value='';try{const r=await api.post('auth/token/',{username:username.value,password:password.value});access.value=r.data.access;localStorage.setItem('techbok_access',r.data.access);if(r.data.refresh)localStorage.setItem('techbok_refresh',r.data.refresh);await loadData();await refreshPending();if(stopSync)stopSync();stopSync=startSyncListeners(async result=>{await refreshPending();if(result?.sent){syncMessage.value=`Synchronised ${result.sent} operation(s).${result.rejected?` ${result.rejected} record(s) need attention.`:''}`;await loadData()}else if(result?.rejected)syncMessage.value=`${result.rejected} offline record(s) need attention. Check branch access, course status and duplicate enrollments.`;else if(result?.error)syncMessage.value=result.error},me.value?.id)}catch(e){error.value='Login failed. Check your username and password.'}finally{loading.value=false}}
function logout(){if(stopSync){stopSync();stopSync=null}access.value='';username.value='';password.value='';error.value='';syncMessage.value='';me.value=null;branches.value=[];courses.value=[];students.value=[];admissions.value=[];enrollments.value=[];localStorage.removeItem('techbok_access');localStorage.removeItem('techbok_refresh');clearOfflineSnapshot().catch(()=>{})}
function resetStudentForm(){editingStudentId.value=null;studentForm.value={branch:String(branches.value[0]?.id||''),first_name:'',middle_name:'',last_name:'',email:'',phone:'',date_of_birth:'',gender:'',address:'',guardian_name:'',guardian_phone:'',status:'active'}}
function editStudent(s){if(!online.value){recordMessage.value='Student profile edits require a live connection. New student records can still be captured offline.';return}editingStudentId.value=s.id;studentForm.value={branch:String(s.branch),first_name:s.first_name,middle_name:s.middle_name||'',last_name:s.last_name,date_of_birth:s.date_of_birth||'',gender:s.gender||'',email:s.email||'',phone:s.phone||'',address:s.address||'',guardian_name:s.guardian_name||'',guardian_phone:s.guardian_phone||'',status:s.status||'active'}}
function resetAdmissionForm(){admissionForm.value={branch:String(branches.value[0]?.id||''),course:String(courses.value.find(x=>x.status==='active')?.id||''),intake:'',first_name:'',middle_name:'',last_name:'',email:'',phone:'',date_of_birth:'',gender:'',address:'',guardian_name:'',guardian_phone:''}}
async function createRecord(type){
 recordBusy.value=true;recordMessage.value=''
 try{
  const forms={students:studentForm.value,admissions:admissionForm.value,enrollments:enrollmentForm.value}
  const payload={...forms[type]}
  if(payload.branch)payload.branch=Number(payload.branch)
  if(payload.course)payload.course=Number(payload.course)
  if(payload.student)payload.student=Number(payload.student)
  Object.keys(payload).forEach(k=>{if(payload[k]==='')delete payload[k]})
  if(!navigator.onLine){
   if(type==='students'&&editingStudentId.value)throw new Error('Student profile edits require a live connection.')
   const entityMap={students:'student_record',admissions:'admission_application',enrollments:'enrollment_record'}
   await queueOfflineOperation({entity_type:entityMap[type],operation:'upsert',payload,branch_id:payload.branch,user_id:me.value?.id})
   recordMessage.value='Saved securely on this device. It will be validated and synchronised when the connection returns.'
   if(type==='students')resetStudentForm()
   if(type==='admissions')resetAdmissionForm()
   if(type==='enrollments')enrollmentForm.value={student:'',branch:'',course:'',cohort:'',start_date:'',expected_end_date:'',tuition_fee:'0',other_fees:'0'}
   await refreshPending()
   return
  }
  if(type==='students'&&editingStudentId.value)await api.patch(`students/${editingStudentId.value}/`,payload)
  else await api.post(type+'/',payload)
  recordMessage.value=type==='students'?(editingStudentId.value?'Student record updated.':'Student record created.'):type==='admissions'?'Admission application submitted.':'Enrollment created.'
  if(type==='students')resetStudentForm()
  if(type==='admissions')resetAdmissionForm()
  if(type==='enrollments')enrollmentForm.value={student:'',branch:'',course:'',cohort:'',start_date:'',expected_end_date:'',tuition_fee:'0',other_fees:'0'}
  await loadData()
 }catch(e){
  if(!e.response){
   if(type==='students'&&editingStudentId.value){recordMessage.value='Student profile edits require a live connection.';return}
   if(navigator.onLine){recordMessage.value='The server did not confirm whether this record was saved. Refresh the directory before trying again to avoid a duplicate.';return}
   const forms={students:studentForm.value,admissions:admissionForm.value,enrollments:enrollmentForm.value}
   const payload={...forms[type]}
   if(payload.branch)payload.branch=Number(payload.branch)
   if(payload.course)payload.course=Number(payload.course)
   if(payload.student)payload.student=Number(payload.student)
   Object.keys(payload).forEach(k=>{if(payload[k]==='')delete payload[k]})
   try{
    const entityMap={students:'student_record',admissions:'admission_application',enrollments:'enrollment_record'}
    await queueOfflineOperation({entity_type:entityMap[type],operation:'upsert',payload,branch_id:payload.branch,user_id:me.value?.id})
    recordMessage.value='Server connection was interrupted. The record has been saved on this device for synchronisation.'
    if(type==='students')resetStudentForm()
    if(type==='admissions')resetAdmissionForm()
    if(type==='enrollments')enrollmentForm.value={student:'',branch:'',course:'',cohort:'',start_date:'',expected_end_date:'',tuition_fee:'0',other_fees:'0'}
    await refreshPending()
   }catch(queueError){recordMessage.value=queueError.message||'Could not save this record offline.'}
  }else{
   const d=e.response?.data
   recordMessage.value=typeof d==='string'?d:(d?.detail||Object.entries(d||{}).map(([k,v])=>`${k}: ${Array.isArray(v)?v.join(', '):v}`).join(' · ')||'Could not save this record.')
  }
 }finally{recordBusy.value=false}
}
async function reviewAdmission(a,status){
 const note=status==='rejected'?'Application not approved.':a.review_notes||''
 try{await api.post(`admissions/${a.id}/review/`,{status,review_notes:note});recordMessage.value=`${a.application_number} updated to ${status.replace('_',' ')}.`;await loadData()}
 catch(e){recordMessage.value=e.response?.data?.detail||'Could not update admission status.'}
}
async function updateEnrollmentStatus(enrollment,newStatus){
 try{await api.patch(`enrollments/${enrollment.id}/`,{status:newStatus});recordMessage.value=`${enrollment.enrollment_number} updated to ${newStatus}.`;await loadData()}
 catch(e){recordMessage.value=e.response?.data?.detail||'Could not update enrollment status.'}
}
async function convertAdmission(a){
 if(!confirm(`Convert ${a.application_number} into a student record and course enrollment?`))return
 try{const r=await api.post(`admissions/${a.id}/convert/`,{});recordMessage.value=`Created ${r.data.student.student_number} and ${r.data.enrollment.enrollment_number}.`;await loadData()}
 catch(e){recordMessage.value=e.response?.data?.detail||'Could not convert this application.'}
}
function updateEnrollmentBranch(){const s=students.value.find(x=>String(x.id)===String(enrollmentForm.value.student));if(s)enrollmentForm.value.branch=String(s.branch)}
function updateEnrollmentCourse(){const c=courses.value.find(x=>String(x.id)===String(enrollmentForm.value.course));if(c){enrollmentForm.value.tuition_fee=String(c.tuition_fee||0);enrollmentForm.value.other_fees=String(c.other_fees||0)}}
onMounted(async()=>{window.addEventListener('online',()=>online.value=true);window.addEventListener('offline',()=>online.value=false);window.addEventListener('techbok-outbox-changed',refreshPending);if(access.value){await loadData();await refreshPending();stopSync=startSyncListeners(async result=>{await refreshPending();if(result?.sent){syncMessage.value=`Synchronised ${result.sent} operation(s).${result.rejected?` ${result.rejected} record(s) need attention.`:''}`;await loadData()}else if(result?.rejected)syncMessage.value=`${result.rejected} offline record(s) need attention. Check branch access, course status and duplicate enrollments.`;else if(result?.error)syncMessage.value=result.error},me.value?.id)}})
</script>
<template>
  <main v-if="!isLoggedIn" class="login-wrap"><div class="login-card"><img class="login-logo" :src="techbokLogo" alt="TechBoK logo"><p class="eyebrow">TechBoK INSTITUTE</p><h1>Welcome back</h1><p class="muted">Sign in to your staff workspace.</p><form @submit.prevent="login"><label>Username<input v-model="username" autocomplete="off" required placeholder="Enter your username"></label><label>Password<input v-model="password" autocomplete="new-password" type="password" required placeholder="Enter your password"></label><p v-if="error" class="error">{{error}}</p><button class="primary full" :disabled="loading">{{loading?'Signing in…':'Sign in to workspace'}}</button></form><p class="footnote">Secure access for authorised TechBoK personnel</p></div></main>
  <div v-else class="app-shell"><aside class="sidebar"><div class="brand"><img class="sidebar-logo" :src="techbokLogo" alt="TechBoK logo"><div><strong>TechBoK</strong><span>INSTITUTE MANAGEMENT</span></div></div><div class="nav-label">WORKSPACE</div><button v-for="item in [{name:'Overview',icon:LayoutDashboard},{name:'Branches',icon:Building2},{name:'Courses',icon:BookOpen},{name:'Students',icon:GraduationCap},{name:'Access & Audit',icon:ShieldCheck},{name:'Offline Workspace',icon:ShieldCheck}]" :key="item.name" class="nav-item" :class="{selected:activeTab===item.name}" @click="activeTab=item.name"><component :is="item.icon" :size="18"/>{{item.name}}</button><div class="sidebar-bottom"><div class="avatar">{{(me?.first_name||me?.username||'T').slice(0,1).toUpperCase()}}</div><div class="user-label"><strong>{{me?.first_name || me?.username}}</strong><span>{{me?.is_system_admin?'System administrator':'Authorised staff'}}</span></div><button class="icon-button" title="Sign out" @click="logout"><LogOut :size="17"/></button></div></aside>
  <section class="main-area"><header class="topbar"><div><span class="breadcrumb">Workspace /</span> <strong>{{activeTab}}</strong></div><div class="top-actions"><span class="status-dot" :class="{offline:!online}"></span><span>{{online?'Online':'Offline'}}</span><span class="sync-count">{{pending}} pending</span><div class="avatar mini">{{(me?.username||'T').slice(0,1).toUpperCase()}}</div></div></header><div class="content"><div class="page-heading"><div><p class="eyebrow">TechBoK OPERATIONS</p><h1>{{activeTab==='Overview'?'Good day, '+(me?.first_name||me?.username):activeTab}}</h1><p class="muted">A clear view of your institute, people and learning programmes.</p></div><button class="outline" @click="loadData">Refresh data</button></div><p v-if="error" class="error banner">{{error}}</p><div v-if="activeTab==='Overview'" class="stats-grid"><article class="stat-card"><div class="stat-icon blue"><Building2 :size="20"/></div><span>Accessible branches</span><strong>{{branches.length}}</strong><small>Across your assigned locations</small></article><article class="stat-card"><div class="stat-icon gold"><BookOpen :size="20"/></div><span>Courses in catalogue</span><strong>{{courses.length}}</strong><small>Dynamic TechBoK courses</small></article><article class="stat-card"><div class="stat-icon green"><Users :size="20"/></div><span>Your access</span><strong class="access-value">{{me?.is_system_admin?'Administrator':'Staff member'}}</strong><small>Role-based workspace</small></article></div><div v-if="activeTab==='Overview'" class="two-column"><section class="panel"><div class="panel-heading"><div><h2>Branch locations</h2><p>Locations available to your account</p></div><Building2 :size="19"/></div><div v-if="!branches.length" class="empty">No branches available yet. A system administrator can create branches in Django Admin.</div><div v-for="b in branches" :key="b.id" class="list-row"><div class="row-icon"><Building2 :size="18"/></div><div class="row-copy"><strong>{{b.name}}</strong><span>{{b.code}}</span></div><span class="pill" :class="b.is_active?'active':'inactive'">{{b.is_active?'Active':'Inactive'}}</span></div></section><section class="panel"><div class="panel-heading"><div><h2>Course catalogue</h2><p>Programmes configured for TechBoK</p></div><BookOpen :size="19"/></div><div class="search-box"><Search :size="16"/><input v-model="search" placeholder="Search courses or codes"></div><div v-if="!filteredCourses.length" class="empty">No matching courses. An authorised staff member can create courses through the API or Django Admin.</div><div v-for="c in filteredCourses.slice(0,5)" :key="c.id" class="list-row"><div class="row-icon book"><BookOpen :size="18"/></div><div class="row-copy"><strong>{{c.name}}</strong><span>{{c.code}} · {{c.delivery_mode.replace('_',' ')}}</span></div><span class="pill" :class="c.status==='active'?'active':'inactive'">{{c.status}}</span></div></section></div><section v-if="activeTab==='Access & Audit'" class="notice-panel"><ShieldCheck :size="24"/><div><h2>Access control and audit foundation</h2><p>Branch memberships and audit events are enforced by the API. Audit history is currently available to system administrators through <code>/api/audit/</code>. Detailed permission administration and a dedicated audit viewer are planned for the next milestone.</p></div></section><section v-if="activeTab==='Students'" class="module-layout">
  <div class="panel"><div class="panel-heading"><div><h2>{{editingStudentId?'Update student details':'Register a student'}}</h2><p>{{editingStudentId?'Edit the selected student profile':'Create an official TechBoK student record'}}</p></div><GraduationCap :size="19"/></div>
   <form class="record-form" @submit.prevent="createRecord('students')">
    <label>Branch<select v-model="studentForm.branch" required><option value="" disabled>Select branch</option><option v-for="b in branches" :key="b.id" :value="String(b.id)">{{b.name}}</option></select></label>
    <div class="form-grid"><label>First name<input v-model="studentForm.first_name" required maxlength="100"></label><label>Middle name<input v-model="studentForm.middle_name"></label><label>Last name<input v-model="studentForm.last_name" required></label><label>Date of birth<input v-model="studentForm.date_of_birth" type="date"></label><label>Gender<select v-model="studentForm.gender"><option value="">Not specified</option><option value="female">Female</option><option value="male">Male</option></select></label><label>Email<input v-model="studentForm.email" type="email"></label><label>Phone<input v-model="studentForm.phone"></label><label>Guardian name<input v-model="studentForm.guardian_name"></label><label>Guardian phone<input v-model="studentForm.guardian_phone"></label><label>Student status<select v-model="studentForm.status"><option value="active">Active</option><option value="inactive">Inactive</option><option value="graduated">Graduated</option><option value="withdrawn">Withdrawn</option></select></label></div>
    <label>Residential address<textarea v-model="studentForm.address" rows="2"></textarea></label>
    <div class="form-actions"><button class="primary" :disabled="recordBusy || !branches.length">{{recordBusy?'Saving…':editingStudentId?'Save student changes':'Create student record'}}</button><button v-if="editingStudentId" type="button" class="outline" @click="resetStudentForm">Cancel edit</button></div>
   </form>
  </div>
  <div class="panel"><div class="panel-heading"><div><h2>Student directory</h2><p>{{students.length}} student record(s) in your accessible branches</p></div><Users :size="19"/></div>
   <div class="search-box"><Search :size="16"/><input v-model="search" placeholder="Search name, student number, email or phone"></div>
   <div v-if="!filteredStudents.length" class="empty">No student records found. Register the first student using the form.</div>
   <div v-for="s in filteredStudents" :key="s.id" class="list-row"><div class="row-icon"><GraduationCap :size="18"/></div><div class="row-copy"><strong>{{s.full_name}}</strong><span>{{s.student_number}} · {{s.branch_name}} · {{s.phone||'No phone'}}</span></div><span class="pill" :class="s.status==='active'?'active':'inactive'">{{s.status}}</span><button class="outline edit-record" :disabled="!online" @click="editStudent(s)">Edit</button></div>
  </div>
 </section>
 <section v-if="activeTab==='Admissions'" class="module-layout">
  <div class="panel"><div class="panel-heading"><div><h2>New admission application</h2><p>Capture an applicant for review</p></div><UserPlus :size="19"/></div>
   <form class="record-form" @submit.prevent="createRecord('admissions')">
    <div class="form-grid"><label>Branch<select v-model="admissionForm.branch" required><option value="" disabled>Select branch</option><option v-for="b in branches" :key="b.id" :value="String(b.id)">{{b.name}}</option></select></label><label>Course<select v-model="admissionForm.course" required><option value="" disabled>Select course</option><option v-for="c in courses.filter(x=>x.status==='active')" :key="c.id" :value="String(c.id)">{{c.name}}</option></select></label><label>Intake / cohort<input v-model="admissionForm.intake" placeholder="e.g. November 2026"></label><label>First name<input v-model="admissionForm.first_name" required></label><label>Middle name<input v-model="admissionForm.middle_name"></label><label>Last name<input v-model="admissionForm.last_name" required></label><label>Date of birth<input v-model="admissionForm.date_of_birth" type="date"></label><label>Gender<select v-model="admissionForm.gender"><option value="">Not specified</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option><option value="not_stated">Prefer not to say</option></select></label><label>Email<input v-model="admissionForm.email" type="email"></label><label>Phone<input v-model="admissionForm.phone"></label><label>Guardian name<input v-model="admissionForm.guardian_name"></label><label>Guardian phone<input v-model="admissionForm.guardian_phone"></label></div>
    <label>Address<textarea v-model="admissionForm.address" rows="2"></textarea></label>
    <button class="primary" :disabled="recordBusy || !branches.length || !courses.some(x=>x.status==='active')">{{recordBusy?'Saving…':'Submit application'}}</button>
   </form>
  </div>
  <div class="panel"><div class="panel-heading"><div><h2>Applications</h2><p>{{admissions.length}} application(s)</p></div><ClipboardList :size="19"/></div>
   <div class="search-box"><Search :size="16"/><input v-model="search" placeholder="Search applicant, reference or course"></div>
   <div v-if="!filteredAdmissions.length" class="empty">No admission applications found.</div>
   <article v-for="a in filteredAdmissions" :key="a.id" class="record-item"><div class="row-copy"><strong>{{a.applicant_name}}</strong><span>{{a.application_number}} · {{a.course_name}} · {{a.branch_name}}</span><span>{{a.intake||'No intake specified'}} · {{a.application_date}}</span></div><span class="pill" :class="a.status==='accepted'?'active':'inactive'">{{a.status.replace('_',' ')}}</span><div v-if="!a.converted_student" class="record-actions"><button v-if="a.status==='submitted'" class="outline" :disabled="!online" @click="reviewAdmission(a,'under_review')">Start review</button><button v-if="['submitted','under_review'].includes(a.status)" class="outline" :disabled="!online" @click="reviewAdmission(a,'accepted')">Accept</button><button v-if="['submitted','under_review'].includes(a.status)" class="outline danger" :disabled="!online" @click="reviewAdmission(a,'rejected')">Reject</button><button v-if="a.status==='accepted'" class="primary small-button" :disabled="!online" @click="convertAdmission(a)">Convert to student</button></div><span v-else class="conversion-note">Converted to {{a.converted_student}}</span></article>
  </div>
 </section>
 <section v-if="activeTab==='Enrollments'" class="module-layout">
  <div class="panel"><div class="panel-heading"><div><h2>Create enrollment</h2><p>Assign a registered student to a course</p></div><Layers :size="19"/></div>
   <form class="record-form" @submit.prevent="createRecord('enrollments')">
    <label>Student<select v-model="enrollmentForm.student" @change="updateEnrollmentBranch" required><option value="" disabled>Select student</option><option v-for="s in students" :key="s.id" :value="String(s.id)">{{s.student_number}} — {{s.full_name}}</option></select></label>
    <label>Course<select v-model="enrollmentForm.course" @change="updateEnrollmentCourse" required><option value="" disabled>Select course</option><option v-for="c in courses.filter(x=>x.status==='active')" :key="c.id" :value="String(c.id)">{{c.name}}</option></select></label>
    <label>Cohort / intake<input v-model="enrollmentForm.cohort" placeholder="e.g. November 2026"></label>
    <div class="form-grid"><label>Start date<input v-model="enrollmentForm.start_date" type="date"></label><label>Expected end date<input v-model="enrollmentForm.expected_end_date" type="date"></label><label>Tuition fee<input v-model="enrollmentForm.tuition_fee" type="number" min="0" step="0.01" required></label><label>Other fees<input v-model="enrollmentForm.other_fees" type="number" min="0" step="0.01" required></label></div>
    <p class="form-hint">The enrollment branch is taken from the selected student's registered branch.</p>
    <button class="primary" :disabled="recordBusy || !students.length || !courses.some(x=>x.status==='active')">{{recordBusy?'Saving…':'Create enrollment'}}</button>
   </form>
  </div>
  <div class="panel"><div class="panel-heading"><div><h2>Enrollment register</h2><p>{{enrollments.length}} enrollment(s)</p></div><Layers :size="19"/></div>
   <div class="search-box"><Search :size="16"/><input v-model="search" placeholder="Search student, enrollment or course"></div>
   <div v-if="!filteredEnrollments.length" class="empty">No enrollments found.</div>
   <div v-for="e in filteredEnrollments" :key="e.id" class="list-row"><div class="row-icon book"><BookOpen :size="18"/></div><div class="row-copy"><strong>{{e.student_name}}</strong><span>{{e.enrollment_number}} · {{e.course_name}} · {{e.cohort||'No cohort'}}</span><span>{{e.branch_name}} · ₦{{Number(e.tuition_fee).toLocaleString()}}</span></div><select class="status-select" :value="e.status" :disabled="!online" @change="updateEnrollmentStatus(e,$event.target.value)"><option value="pending">Pending</option><option value="active">Active</option><option value="completed">Completed</option><option value="deferred">Deferred</option><option value="withdrawn">Withdrawn</option></select></div>
  </div>
 </section>
 <p v-if="recordMessage && ['Students','Admissions','Enrollments'].includes(activeTab)" class="record-feedback">{{recordMessage}}</p><section v-if="activeTab==='Offline Workspace'" class="panel offline-panel"><div class="panel-heading"><div><h2>Offline capture workspace</h2><p>Test the local outbox while the server is unavailable.</p></div><ShieldCheck :size="19"/></div><div class="offline-banner" :class="online?'online':'offline'"><strong>{{online?'Connection available':'Working offline'}}</strong><span>{{pending}} pending operation(s) stored in this browser on this device.</span></div><div v-if="attentionItems.length" class="sync-attention"><strong>{{attentionItems.length}} record(s) need attention</strong><p v-for="item in attentionItems" :key="item.event_id">{{item.entity_type.replace('_',' ')}} · {{item.error}}</p><small>These records were not uploaded. Correct the issue and create a new submission; rejected items are retained locally for reference.</small></div><form class="offline-form" @submit.prevent="saveOfflineDraft"><label>Draft title<input v-model="draftTitle" required maxlength="120" placeholder="e.g. Student admission follow-up"></label><label>Note<textarea v-model="draftNote" required rows="4" maxlength="2000" placeholder="Capture a note to test offline saving and synchronisation"></textarea></label><button class="primary" type="submit">Save on this device</button></form><p v-if="syncMessage" class="muted sync-message">{{syncMessage}}</p><p class="offline-warning">Foundation test only: this sample draft is synchronised as an acknowledged operation envelope. It is not yet written into the official student/admissions tables. Domain-specific handlers will be added with those modules.</p></section><section v-if="activeTab==='Branches'" class="notice-panel"><Building2 :size="24"/><div><h2>Branch management</h2><p>Branch creation and branch setting changes are restricted to system administrators. Use Django Admin for this starter milestone; a dedicated management screen will follow.</p></div></section><section v-if="activeTab==='Courses'" class="notice-panel"><BookOpen :size="24"/><div><h2>Dynamic course catalogue</h2><p>Courses are stored in the database, not hard-coded. The API supports course creation and editing for authorised staff. A full course editor will follow in the next UI milestone.</p></div></section><footer>© {{new Date().getFullYear()}} TechBoK · Institute Management Platform <span>Built for clarity and accountability</span></footer></div></section></div>
</template>
