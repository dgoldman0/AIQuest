// Source code uses examples from https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications

ws = null;
status = "connecting";
username = ""

function htmlEncode(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

async function send_message(msg) {
  await ws.send(msg)
}

function print_player(f, message, uname = null) {
  if (uname == null) {
    uname = username
  }
  converter = new showdown.Converter()
  f.innerHTML += `<hr/><div class = "player-block">${uname}: ${converter.makeHtml(message)}</div>`
}

function print_narration(f, message) {
  converter = new showdown.Converter()
  f.innerHTML += `<hr/><div class = "narration-block">${converter.makeHtml(message)}</div>`
}

function print_notice(f, notice) {
  f.innerHTML += `<hr/>System Notice: ${notice}`
}

$(document).ready(function() {
  const f = document.getElementById("chat-history");
  f.innerHTML = "AIQuest Console..."
  const urlParams = new URLSearchParams(window.location.search);
  url = "ws://localhost:9289"
  activity = null;

  if ("WebSocket" in window) {
    onclose = function(event) {
      status = "connecting"
      activity = null
      print_notice("Connection lost...")
    };

    onmessage = async function(event) {
          console.log(event)
          msg = await event.data;
          if (msg.startsWith("SYSTEM:")) {
            if (msg == "SYSTEM:MALICIOUS") {
              print_notice(f, "The system has detected that your message may be malicious...")
            } else if (msg == "SYSTEM:PROCESSING") {
              status = "waiting"
            } else if (msg.startsWith("PLAYER:")) {
              cut = msg.indexOf("!")
              player = msg.substring(7, cut)
              msg = msg.substring(cut + 1)
              print_player(f, msg, player)
            }
          } else {
            switch (status) {
              case 'connecting':
              if (msg == "AIQuest") {
                print_notice(f, "Connected to AIQuest")
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
                if (msg == "SUCCESS") {
                  print_notice(f, "Authentication successful...")
                  status = "connected";
                } else if (msg == "INVALID" || msg == "UNKNOWN") {
                  f.innerHTML += "<hr/>Unable to connect: Invalid login credentials."
                } else if (msg == "BLOCKED") {
                  f.innerHTML += "<hr/>Unable to connect: User is blocked from accessing SAM."
                }
              } else if (activity == "register") {
                // Neither of these tables are disabled after selection. Need to really clean things up properly.
                if (msg.startsWith("REALMS:")) {
                  f.innerHTML += "<br/>Select Starting Realm"
                  realms = JSON.parse(msg.substring(7))
                  html = "<br/><table id = 'realmselect' class = 'styled-table'><tr><th>Realm</th><th>Description</th></tr>"
                  for (realm of realms) {
                    html += "<tr onclick = 'send_message(" + realm[0] + ");'><td>" + realm[1] + "</td><td>" + realm[2] + "</td></tr>"
                  }
                  f.innerHTML += html
                } else if (msg.startsWith("CLANS:")) {
                  f.innerHTML += "<br/>Select Starting Clan"
                  clans = JSON.parse(msg.substring(6))
                  html = "<br/><table id = 'clanselection' class = 'styled-table'><tr><th>Clan</th><th>Description</th></tr>"
                  for (clan of clans) {
                    html += "<tr onclick = 'send_message(" + clan[0] + ");'><td>" + clan[1] + "</td><td>" + clan[2] + "</td></tr>"
                  }
                  f.innerHTML += html
                } else if (msg == "SUCCESS") {
                  status = "connected"
                  f.innerHTML += "<hr/>Registration Complete."
                  status = "synopsis";
                }
              }
              break;
              case 'waiting':
              if (msg == "SYSTEM:FINISHED") {
                status = "active"
              } else {
                if (msg.startsWith("NARRATION:")) {
                  print_narration(f, msg.slice(10))
                }
              }
              break;
              default:
              if (msg == "WELCOME") {
                f.innerHTML += "<hr/>You may now interact with the world..."
                status = "active"
              } else if (msg.startsWith("NARRATION:")) {
                print_narration(f, msg.slice(10))
              } else if (msg.startsWith("STATUS:")){
                print_notice(f, htmlEncode(msg.slice(7)))
              }
            }
          }
          f.scrollTop = f.scrollHeight
        };

    $("#chat-form").submit(async function(e) {
      e.preventDefault();
      input = $("#msg");
      msg = input.val();
      input.val("")
      if (status != "synopsis" && status != "waiting") {
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
            f.innerHTML += `<hr/>COMMAND: ${htmlEncode(msg.substring(1))}`;
            f.scrollTop = f.scrollHeight
          }
        } else {
          status = "waiting"
          print_player(f, htmlEncode(msg))
          f.scrollTop = f.scrollHeight
          await ws.send("MSG:" + msg);
        }
      }
      input.focus();
      return false;
    });
  } else {
    // the browser doesn't support WebSocket.
    alert("Websockets not supported.")
  }
});
