chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_MICROPHONE') {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      const tab = tabs[0];
      chrome.tabs.sendMessage(tab.id, {type: 'REQUEST_MICROPHONE'}, (response) => {
        sendResponse(response);
      });
    });
    return true;
  }
});
