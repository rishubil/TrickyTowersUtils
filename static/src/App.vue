<template>
  <div class="container">
    <div id="overlayContainer">
      <img class="bg" src="/assets/img/test3.jpg">
      <PlayerNames :players="gamedata.players"></PlayerNames>
    </div>
  </div>
</template>

<script>
import PlayerNames from "/components/PlayerNames.vue";
import createToast from "/js/utils.js";
import _ from "lodash";
import io from "socket.io-client";

export default {
  name: "App",
  components: {
    PlayerNames
  },
  data() {
    return {
      socket: null,
      gamedata: {
        // test data
        game_info: {
          is_playing: true,
          is_finished: false,
          game_mode: "SURVIVAL_NORMAL",
          game_type: "MULTIPLAYER_ONLINE",
          cup_type: "ONLINE",
          target_score: 9
        },
        players: [
          {
            username: "KoreanTrickyTowersUnion",
            id: "KEYBOARD",
            steam_id: 76561198069404530,
            elo: 1000144,
            is_online: true,
            medals: [3, 2],
            total_score: 5
          },
          {
            username: "한국어이름",
            id: "RemotePlayer3",
            steam_id: 76561198273117810,
            elo: 1000123,
            is_online: true,
            medals: [2, 3],
            total_score: 5
          },
          {
            username: "123",
            id: "RemotePlayer5",
            steam_id: 76561198152298180,
            elo: 1000012,
            is_online: true,
            medals: [1, 1],
            total_score: 2
          }
        ]
      }
    };
  },
  methods: {
    connectSocket() {
      console.info("Trying to connect server...");
      this.socket = io.connect(
        "http://" + document.domain + ":" + location.port
      );
    },
    initSocket() {
      this.connectSocket();
      this.socket.on("connect", function() {
        console.info("Connected to server");
      });
      this.socket.on("json", function(data) {
        this.gamedata = data;
      });
      this.socket.on("disconnect", function() {
        console.info("Disconnected to server");
        console.info("Trying to reconnect after 3 sec...");
        _.delay(this.connectSocket, 3000);
      });
    }
  },
  created() {
    this.initSocket();
  }
};
</script>

<style scoped>
#overlayContainer {
  width: 100vw;
  height: 56.25vw;
  max-width: 100%;
}

#overlayContainer .bg {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
}
</style>

<style>
@import url("https://fonts.googleapis.com/css?family=Noto+Sans+JP:400,700|Noto+Sans+KR:400,700|Noto+Sans+SC:400,700|Noto+Sans+TC:400,700|Noto+Sans:400,700&subset=chinese-simplified,chinese-traditional,cyrillic,cyrillic-ext,devanagari,greek,greek-ext,japanese,korean,latin-ext,vietnamese");

* {
  font-family: "Noto Sans KR", "Noto Sans JP", "Noto Sans SC", "Noto Sans TC",
    "Noto Sans", sans-serif;
  -webkit-font-smoothing: antialiased;
}

p {
  margin: 0;
}

body {
  margin: 0;
  overflow-y: hidden;
}

.hidden {
  opacity: 0;
}
</style>
