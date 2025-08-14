// E2E flow runner for backend API (login, diagnostic, plan)
// Usage: node tools/e2e_flow.js

const baseUrl = process.env.API_URL || 'http://localhost:4000';

async function postForm(path, form) {
  const body = new URLSearchParams(form).toString();
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status} ${res.statusText}`);
  return res.json();
}

async function postJson(path, data, token) {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`POST ${path} failed: ${res.status} ${res.statusText} ${text}`);
  }
  return res.json();
}

async function getJson(path, token) {
  const res = await fetch(`${baseUrl}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  return res.json();
}

(async () => {
  const output = { baseUrl };
  try {
    // Health
    output.health = await getJson('/health');

    // Login admin
    const login = await postForm('/api/v1/auth/login', { username: 'admin', password: 'secret' });
    output.user = login.user || null;
    const token = login.access_token;
    if (!token) throw new Error('No access_token in login response');

    // Subjects for diagnostic
    const subjects = await getJson('/api/v1/diagnostic/subjects', token);
    output.subjectsCount = Array.isArray(subjects) ? subjects.length : (subjects.subjects?.length ?? 0);
    const subject = Array.isArray(subjects) ? subjects.find(s => s.name === 'Matemáticas') || subjects[0] : (subjects.subjects?.[0]);
    if (!subject) throw new Error('No subjects available');

    // Create diagnostic test
    const created = await postJson('/api/v1/diagnostic/tests', { subject_id: subject.id, test_type: 'real_icfes' }, token);
    output.createdTest = created;
    const testId = created.id || created.test_id;
    if (!testId) throw new Error('No test id returned');

    // Fetch questions
    const questions = await getJson(`/api/v1/diagnostic/tests/${testId}/questions`, token);
    const qList = Array.isArray(questions) ? questions : questions.questions;
    output.questionsCount = qList?.length ?? 0;
    if (!qList || qList.length === 0) throw new Error('No questions returned');

    // Submit first 10 answers as A
    const answers = qList.slice(0, 10).map(q => ({
      question_id: q.id,
      user_answer: 'A',
      response_time_ms: 5000
    }));
    const submit = await postJson(`/api/v1/diagnostic/tests/${testId}/submit`, { answers }, token);
    output.analysis = submit;

    // Generate study plan based on diagnostic
    const plan = await postJson(`/api/v1/study-plans/generate/${subject.id}?use_diagnostic=true`, {}, token);
    output.planTitle = plan.title || plan.plan_name || 'generated';
    output.planUnits = plan.units?.length ?? plan.total_units ?? 0;

    // Recommendations
    const reco = await getJson(`/api/v1/study-plans/recommendations/${subject.id}`, token);
    output.recommendations = reco;

    console.log(JSON.stringify({ ok: true, output }, null, 2));
  } catch (err) {
    console.error(JSON.stringify({ ok: false, error: String(err), output }, null, 2));
    process.exit(1);
  }
})();
