var config = null;
var data = null;

function ready(fn) {
    if (document.attachEvent ? document.readyState === "complete" : document.readyState !== "loading") {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

function hasClass(el, className) {
    if (el.classList) {
        return el.classList.contains(className);
    } else {
        return new RegExp('(^| )' + className + '( |$)', 'gi').test(el.className);
    }
}

function addClass(el, className) {
    if (el.classList) {
        el.classList.add(className);
    } else {
        el.className += ' ' + className;
    }
}

function removeClass(el, className) {
    if (el.classList) {
        el.classList.remove(className);
    } else {
        el.className = el.className.replace(new RegExp('(^|\\b)' + className.split(' ').join('|') + '(\\b|$)', 'gi'), ' ');
    }
}

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
    config = newConfig;
    console.log('config updated:');
    console.log(config);
}

function updateData(newData) {
    data = newData;
    console.log('data updated:');
    console.log(data);
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

function initSocket() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('connect', function () {
        console.log('socket connected');
        hideMessage('socketNotConnectedMsgBox');
    });
    socket.on('json', function (data) {
        updateData(data);
    });
    socket.on('disconnect', function () {
        console.log('socket disconnected');
        showMessage('socketNotConnectedMsgBox');
    });
}

function vwToPx(vw) {
    return document.documentElement.clientWidth / 100 * vw;
}

function initFitty() {
    document.fonts.ready.then(function () {
        fitty.observeWindow = false;
        var nameFittys = null;
        function SetFitty() {
            nameFittys = fitty('.player-name-box .name > p', {
                minSize: vwToPx(0.4),
                maxSize: vwToPx(1.6),
                multiLine: false,
                observeWindow: false
            });
        }
        SetFitty();
        window.addEventListener('resize', function () {
            for (var i = 0; i < nameFittys.length; i++) {
                nameFittys[i].unsubscribe();
            }
            SetFitty();
        }, true);
    });
}

ready(function () {
    initFitty();
    getConfig();
    initSocket();
});

