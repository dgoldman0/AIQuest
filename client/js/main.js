// Source code uses examples from https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications


function htmlEncode(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

$(document).ready(function() {
  const urlParams = new URLSearchParams(window.location.search);
  // Yes I know this isn't a secure way to do things, but for now it's fine and I'm too exhausted to create a better system.
  username = "GUEST"
  password = ""
  url = "ws://localhost:9289"
  ws = null;
  status = "connecting";
  activity = null;

  if ("WebSocket" in window) {
    onclose = function(event) {
      if (event.wasClean) {
        status = "connecting"
        activity = null;
      } else {
        // e.g. server process killed or network down
        // event.code is usually 1006 in this case
        console.log('[close] Connection died');
      }
    };

    onmessage = async function(event) {
          console.log(event)
          msg = await event.data;
          // Change status system so that it differentiates between login and registration.
          switch (status) {
            case 'connecting':
            if (msg == "AIQuest") {
              f.innerHTML += "<br/>System Notice: Connected to AIQuest"
            } else {
            }
            break;
            case 'salt':
            if (msg.startsWith("CHALLENGE:$2b")) {
              // The 2a replacement is due to salt version. See https://github.com/ircmaxell/password_compat/issues/49
              salt = "$2y" + msg.substring(13);
              hashed_pw = dcodeIO.bcrypt.hashSync(password, salt);
              hashed_pw = "$2b" + hashed_pw.slice(3);
              status = "verifying";
              await ws.send(hashed_pw);
            } else if (msg == "EXISTINGUSER") {
              ws.close();
            }
            break;
            case 'verifying':
            if (activity == "login") {
              if (msg == "WELCOME") {
                f.innerHTML += "Connection Established."
                status = "connected";
              } else if (msg == "INVALID" || msg == "UNKNOWN") {
                f.innerHTML += "Unable to connect: Invalid login credentials."
              } else if (msg == "BLOCKED") {
                f.innerHTML += "Unable to connect: User is blocked from accessing SAM."
              }
            } else if (activity == "register") {
              status = "realms";
              if (msg.startWith("REALMS:")) {
                f.innerHTML += "<br/>System Notice: Registered. Continuing to character creation..."
                console.log(msg.substring(7))
              }
            }
            break;
            default:
              if (msg.startsWith("MSG:")) {
                f.innerHTML += `<br/>&lt;SAM&gt;: ${htmlEncode(msg.slice(4))}`;
              } else if (msg.startsWith("STATUS:")){
                f.innerHTML += `<br/>System Notice: ${htmlEncode(msg.slice(7))}`;
              }
          }
        };

    const f = document.getElementById("chat-history");
    f.innerHTML = "AIQuest Console..."

    $("#chat-form").submit(async function(e) {
      e.preventDefault();
      input = $("#msg");
      msg = input.val();
      input.val("")
      if (msg.startsWith("/")) {
        args = msg.slice(1).split(" ")
        command = args[0].toUpperCase();
        switch (command) {
          case 'CLEAR':
          f.innerHTML = "AIQuest Console..."
          return false
          break;
          case 'QUIT':
          ws.close();
          break;
          case 'LOGIN':
          if (status != "connected") {
            username = args[1]
            password = args[2]
            activity = "login"
            status = "salt"
            ws = new WebSocket(url);
            ws.onmessage = onmessage
            ws.onclose = onclose
            ws.onopen = async function(event) {
              await ws.send("AUTH:" + username);
            }
          } else {
            f.innerHTML += "<br/>System Notice: Already Connected"
          }
          break;
          case 'REGISTER':
          if (status != "connected") {
            username = args[1]
            password = args[2]
            activity = "register"
            status = "salt"
            ws = new WebSocket(url);
            ws.onmessage = onmessage
            ws.onclose = onclose
            ws.onopen = async function(event) {
              await ws.send("REGISTER:" + username);
            }
           } else {
            f.innerHTML += "<br/>System Notice: Already Connected"
          }
          break;
          default:
          await ws.send("COMMAND:" + command);
          break;
        }
      } else {
        await ws.send("MSG:" + msg);
      }
      f.innerHTML += `<br/>${htmlEncode(msg)}`;
      input.focus();
      return false;
    });
  } else {
    // the browser doesn't support WebSocket.
    alert("Websockets not supported.")
  }
});
