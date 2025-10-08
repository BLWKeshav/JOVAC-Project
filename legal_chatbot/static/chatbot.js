// Chat interaction script
async function startConversation() {
  // auto-trigger greeting
  let res = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({message: ''})
  });
  const data = await res.json();
  appendMessage('Bot', data.response);
}

document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('userInput').addEventListener('keypress', function(e){
  if (e.key === 'Enter') sendMessage();
});

async function sendMessage(){
  const input = document.getElementById('userInput');
  const text = input.value.trim();
  if (!text) return;
  appendMessage('You', text);
  input.value = '';
  const res = await fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({message: text})
  });
  const data = await res.json();
  if (data.type === 'text'){
    appendMessage('Bot', data.response);
  } else if (data.type === 'preview'){
    appendMessage('Bot', 'Here is the draft preview:');
    showPreview(data.response, data.pdf_url);
  }
}

function appendMessage(sender, text){
  const box = document.getElementById('chatbox');
  const wrap = document.createElement('div');
  wrap.className = 'msg';
  wrap.innerHTML = `<div class="sender">${sender}:</div><div class="text">${text}</div>`;
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
}

function showPreview(htmlText, pdfUrl){
  const area = document.getElementById('generatedDoc');
  area.innerHTML = `<div class="preview">${htmlText}</div>
                    <a class="link-btn" href="${pdfUrl}" target="_blank">Download PDF</a>
                    <p style="font-size:12px;color:#6b7280;margin-top:8px;">Note: PDF will download the same content shown in preview.</p>`;
  area.scrollIntoView({behavior:'smooth'});
}

window.onload = startConversation;