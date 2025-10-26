const fileInput = document.getElementById('file');
const sendBtn = document.getElementById('send');
const statusEl = document.getElementById('status');
const preview = document.getElementById('preview');
const result = document.getElementById('result');
const downloadBtn = document.getElementById('download-txt');
const copyBtn = document.getElementById('copy');

fileInput.addEventListener('change', () => {
  const f = fileInput.files[0];
  if (!f) return;
  preview.src = URL.createObjectURL(f);
});

sendBtn.addEventListener('click', async () => {
  const f = fileInput.files[0];
  if (!f) { alert('Select an image first'); return; }
  statusEl.innerText = 'Recognizing... (This may take a moment)';
  const fd = new FormData();
  fd.append('image', f);
  try {
    const res = await fetch('/ocr', { method:'POST', body: fd });
    const data = await res.json();
    if (data.error) {
      statusEl.innerText = 'Error: ' + data.error;
    } else {
      result.innerText = data.text || '';
      statusEl.innerText = 'Done ✅';
    }
  } catch (e) {
    statusEl.innerText = 'Request failed: ' + e.message;
  }
});

downloadBtn.addEventListener('click', () => {
  const text = result.innerText || '';
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'ocr_result.txt';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

copyBtn.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(result.innerText || '');
    alert('Copied!');
  } catch (e) {
    alert('Copy failed: ' + e.message);
  }
});
