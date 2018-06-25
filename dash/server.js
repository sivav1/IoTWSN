const express = require('express')
const app = express()
const bodyParser = require('body-parser');
var awsIot = require('aws-iot-device-sdk');

app.set('view engine', 'ejs')
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));

app.get('/', function (req, res) {
    res.render('index', {s1Temp: 0, s1Gyro: 0});
})

app.post('/', function (req, res) {

    var device = awsIot.device({
        keyPath: '../1ea25c8bd2-private.pem.key',
       certPath: '../1ea25c8bd2-certificate.pem.crt',
         caPath: '../root-CA.crt',
       clientId: 'aws_iot',
           host: 'a1mz0kmfnb67b4.iot.ap-southeast-2.amazonaws.com'
     });

    device
    .on('connect', function() {
        console.log('connect');
        device.subscribe('#');
        res.render('index', {s1Temp: "connect", s1Gyro: 0});
    });

    device
    .on('message', function(topic, payload) {
        console.log('message', topic, payload.toString());
        res.render('index', {s1Temp: payload.toString(), s1Gyro: 0});
    });
})

app.listen(3000, function () {
  console.log('Example app listening on port 3000!')
})