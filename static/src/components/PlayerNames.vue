<template>
  <div class="player-names" :class="playerNumberClass">
    <PlayerNameBox v-for="player in players" :key="player.id" :player="player"></PlayerNameBox>
  </div>
</template>

<script>
import PlayerNameBox from "/components/PlayerNameBox.vue";

export default {
  name: "PlayerNames",
  props: {
    players: Array
  },
  components: {
    PlayerNameBox
  },
  data() {
    return {};
  },
  computed: {
    playerNumberClass: function() {
      return "p" + this.players.length;
    }
  }
};
</script>

<style scoped>
.player-names {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 4.5vw;
  -webkit-animation-duration: 1s;
  animation-duration: 1s;
  -webkit-animation-fill-mode: both;
  animation-fill-mode: both;
}

.player-names.p4 .player-name-box:nth-child(1) {
  left: 12.6vw;
  display: block;
}

.player-names.p4 .player-name-box:nth-child(2) {
  left: 35.65vw;
  display: block;
}

.player-names.p4 .player-name-box:nth-child(3) {
  left: 58.7vw;
  display: block;
}

.player-names.p4 .player-name-box:nth-child(4) {
  left: 81.75vw;
  display: block;
}

.player-names.p3 .player-name-box:nth-child(1) {
  left: 16.5vw;
  display: block;
}

.player-names.p3 .player-name-box:nth-child(2) {
  left: 47.3vw;
  display: block;
}

.player-names.p3 .player-name-box:nth-child(3) {
  left: 77.9vw;
  display: block;
}

.player-names.p2 .player-name-box:nth-child(1) {
  left: 24.2vw;
  display: block;
}

.player-names.p2 .player-name-box:nth-child(2) {
  left: 70.3vw;
  display: block;
}
</style>
