var socket = io.connect('http://' + document.domain + ':' + location.port);
socket.on('connect', function () {
    console.log('connected');
});
socket.on('json', function (data) {
    console.log(data);
});
socket.on('disconnect', function () {
    console.log('disconnected');
});