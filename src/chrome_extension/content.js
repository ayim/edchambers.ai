chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'REQUEST_MICROPHONE') {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        sendResponse({ success: true, stream: stream });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true;
  }
});
