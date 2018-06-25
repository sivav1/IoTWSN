var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
var awsIot = require('aws-iot-device-sdk');

app.use(express.static('public'));

server.listen(3000);

app.get('/', function (req, res) {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', function (socket) {

    var topics = ["54:6c:0e:80:57:07/sensor1", "54:6c:0e:80:58:07/sensor2"];
    var firstTopic = true;

    var device = awsIot.device({
        keyPath: '../1ea25c8bd2-private.pem.key',
       certPath: '../1ea25c8bd2-certificate.pem.crt',
         caPath: '../root-CA.crt',
       clientId: 'aws_iot',
           host: 'a1mz0kmfnb67b4.iot.ap-southeast-2.amazonaws.com'
     });

    device
    .on('connect', function() {
        console.log('connected');
        device.subscribe(topics[0]);
    });

    device
    .on('message', function(topic, payload) {
        console.log('message', topic, payload.toString());
        if(firstTopic) {
            device.subscribe(topics[0]);
        } else {
            device.subscribe(topics[1]);
        }
        firstTopic = !firstTopic;
        socket.emit('index', {topic: payload.toString()});
    });
});