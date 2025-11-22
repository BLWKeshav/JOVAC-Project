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
    // Show bot's message if provided, otherwise use default
    const botMsg = data.bot_message || 'All information collected! Your document has been generated successfully.';
    // Immediately show preview button FIRST - appears as soon as all fields collected
    showPreview(data.response, data.preview_url, data.pdf_url, data.doc_type, data.preview_page_url);
    // Then show bot's message
    appendMessage('Bot', botMsg);
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

function showPreview(htmlText, previewUrl, pdfUrl, docType, previewPageUrl){
  const area = document.getElementById('generatedDoc');
  area.innerHTML = `
    <div class="preview-ready-message">
      <div class="success-icon">
        <i class="fa-solid fa-circle-check"></i>
      </div>
      <h3>Document Generated Successfully!</h3>
      <p>Your ${docType ? docType.replace(/_/g, ' ') : 'document'} has been prepared. Click the button below to preview and download.</p>
      <a href="${previewPageUrl || '/preview'}" class="preview-page-btn">
        <i class="fa-solid fa-eye"></i> View Preview & Download
      </a>
    </div>
  `;
  area.scrollIntoView({behavior:'smooth'});
}

window.onload = startConversation;