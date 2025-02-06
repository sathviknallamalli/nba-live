var socket;
var fcastUrl;
fetch("https://fastcast.semfs.engsvc.go.com/public/websockethost")
  .then(function (response) {
    if (response.status !== 200) {
      console.log(
        "Looks like there was a problem. Status Code: " + response.status
      );
      return;
    }

    // Examine the text in the response
    response.json().then(function (data) {
      console.log(data);
      var wsUri =
        "wss://" +
        data.ip +
        ":" +
        data.securePort +
        "/FastcastService/pubsub/profiles/12000?TrafficManager-Token=" +
        data.token;
      console.log(wsUri);
      socket = new WebSocket(wsUri);
      socket.onopen = function (event) {
        console.log("socket open: " + event.data);
        socket.send('{"op": "C"}');
      };
      socket.onmessage = function (event) {
        console.log("socket message received from server: " + event.data);
        var data = JSON.parse(event.data);
        console.log("op = " + data.op);
        if (data.op == "C") {
          var msg = {
            op: "S",
            sid: data.sid,
            tc: "event-topevents",
          };
          socket.send(JSON.stringify(msg));
        } else if (data.op == "H") {
          fcastUrl = data.pl;
        }
      };
    });
  })
  .catch(function (err) {
    console.log("Fetch Error :-S", err);
  });
