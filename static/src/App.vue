<template>
  <div class="container">
    <div id="overlayContainer">
      <img class="bg" src="/assets/img/test3.jpg">
      <PlayerNames :players="gamedata.players"></PlayerNames>
    </div>
    <div id="toast">
      <div id="configErrorMsgBox" class="message-box">
        <p>설정 정보를 불러올 수 없습니다.</p>
      </div>
      <div id="socketNotConnectedMsgBox" class="message-box on">
        <p>서버와 연결되지 않았습니다.</p>
      </div>
    </div>
  </div>
</template>

<script>
import PlayerNames from "/components/PlayerNames.vue";

export default {
  name: "App",
  components: {
    PlayerNames
  },
  data() {
    return {
      gamedata: {
        // test data
        is_playing: true,
        is_finished: false,
        game_mode: "SURVIVAL_NORMAL",
        game_type: "MULTIPLAYER_ONLINE",
        cup_type: "ONLINE",
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
        ],
        target_score: 9
      }
    };
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

#toast {
  padding: 16px;
  position: fixed;
  top: 0;
  left: 0;
}

.message-box {
  background: #b7d276b8;
  padding: 16px;
  border-radius: 8px;
  display: none;
}

.message-box.on {
  display: block;
}
</style>
