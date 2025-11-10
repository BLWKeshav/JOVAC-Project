// Helper to call finalize endpoint and open preview in new tab.
async function finalizeAndOpenPreview(collectedData){
  const resp = await fetch('/finalize_document', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(collectedData)
  });
  const res = await resp.json();
  if (res.preview_full_url) {
    window.open(res.preview_full_url, '_blank');
  } else if (res.pdf_b64) {
    const blob = b64toBlob(res.pdf_b64, 'application/pdf');
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  } else {
    alert('PDF generation failed');
  }
}
function b64toBlob(b64Data, contentType='', sliceSize=512){
  const byteCharacters = atob(b64Data);
  const byteArrays = [];
  for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
    const slice = byteCharacters.slice(offset, offset + sliceSize);
    const byteNumbers = new Array(slice.length);
    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }
  return new Blob(byteArrays, {type: contentType});
}
