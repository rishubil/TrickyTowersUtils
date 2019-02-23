var config = null;
var data = null;

function updateMessage(id, text) {
  var msgBox = document.querySelector('#' + id);
  msgBox.textContent = text;
}

function showMessage(id) {
  var msgBox = document.querySelector('#' + id);
  if (!hasClass(msgBox, 'on')) {
    addClass(msgBox, 'on');
  }
}

function hideMessage(id) {
  var msgBox = document.querySelector('#' + id);
  if (hasClass(msgBox, 'on')) {
    removeClass(msgBox, 'on');
  }
}

function updateConfig(newConfig) {
  if (_.isEqual(config, newConfig)) {
    return;
  }
  var oldConfig = config;
  config = newConfig;
  console.log('config updated:');
  console.log(config);
}

function updateData(newData) {
  if (_.isEqual(data, newData)) {
    return;
  }
  var oldData = data;
  data = newData;
  console.log('data updated:');
  console.log(data);
  checkDiff(oldData, newData);
}

function checkDiff(oldData, newData) {
  checkIsPlaying(oldData, newData);
  checkIsFinished(oldData, newData)
}

function checkIsPlaying(oldData, newData) {
  if (oldData == null) {
    updateIsPlaying(newData.is_playing);
  } else if (oldData.is_playing != newData.is_playing) {
    updateIsPlaying(newData.is_playing);
  }
  return
}

function updateIsPlaying(isPlaying) {
  var playerNames = document.querySelector('.player-names');
  if (isPlaying) {
    removeClass(playerNames, 'hidden');
    updateIsFinished(false);
  } else {
    addClass(playerNames, 'hidden');
  }
}

function checkIsFinished(oldData, newData) {
  if (oldData == null) {
    updateIsFinished(newData.is_finished);
  } else if (oldData.is_finished != newData.is_finished) {
    updateIsFinished(newData.is_finished);
  }
  return
}

function updateIsFinished(isFinished) {
  console.log('updateIsFinished:' + isFinished);
  var playerNames = document.querySelector('.player-names');
  if (isFinished) {
    animate(playerNames, 'slideOutUp')
  } else {
    animate(playerNames, 'slideInDown');
  }
}

function animate(el, animationName, makeHidden) {
  function onAnimationEnd() {
    removeClass(this, 'animated');
    removeClass(this, animationName);
    if (makeHidden) {
      addClass('hidden');
    }
  }
  if (makeHidden == undefined) {
    makeHidden = false;
  }
  removeClass(el, 'hidden');
  removeClass(el, 'animated');
  removeClass(el, animationName);
  addClass(el, 'animated');
  addClass(el, animationName);
  el.addEventListener("webkitAnimationEnd", onAnimationEnd, false);
  el.addEventListener("animationend", onAnimationEnd, false);
  el.addEventListener("oanimationend", onAnimationEnd, false);
}

function getConfig() {
  var request = new XMLHttpRequest();
  request.open('GET', '/overlay_config.json', true);

  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      hideMessage('configErrorMsgBox');
      updateConfig(JSON.parse(request.responseText).config);
    } else {
      showMessage('configErrorMsgBox');
    }
  };

  request.onerror = function () {
    showMessage('configErrorMsgBox');
  };

  request.send();
}

ready(function () {

  getConfig();
  initSocket();
});

