<template>
  <div class="player-names" :class="playerNumberClass">
    <player-item
      v-for="player in filteredPlayers"
      :key="player.id"
      :player="player"
      :isDisplayNames="inPlaying"
      :config="config"
    ></player-item>
  </div>
</template>

<script>
import PlayerItem from "/components/PlayerItem.vue";
import inPlayingMixin from "/js/inPlayingMixin.js";
import _ from "lodash";

export default {
  name: "PlayerHeader",
  mixins: [inPlayingMixin],
  props: {
    players: Array,
    gameInfo: Object,
    config: Object
  },
  components: {
    PlayerItem
  },
  data() {
    return {
      currentRound: 0,
      playerFilter: []
    };
  },
  methods: {
    updateRound(newRound) {
      if (this.currentRound != newRound) {
        this.currentRound = newRound;
        this.updatePlayerFilter();
      }
    },
    updatePlayerFilter() {
      this.playerFilter = _.chain(this.players)
        .filter(player => !player.is_online)
        .map(player => player.id)
        .value();
    },
    initPlayerFilter() {
      this.playerFilter = [];
    }
  },
  computed: {
    filteredPlayers() {
      const vps = _.filter(
        this.players,
        player => _.indexOf(this.playerFilter, player.id) == -1
      );
      const scores = _.reverse(_.map(vps, "total_score").sort());
      return _.map(vps, player => {
        player.rank = _.indexOf(scores, player.total_score) + 1;
        return player;
      });
    },
    playerNumberClass() {
      return "p" + this.filteredPlayers.length;
    }
  },
  watch: {
    players(val) {
      if (this.players.length > 0) {
        const player = this.players[0];
        if (_.isArray(player.medals)) {
          const newRound = player.medals.length + 1;
          this.updateRound(newRound);
        }
      }
    },
    gameInfo(val) {
      if (!this.isPlaying) {
        this.initPlayerFilter();
        this.updateRound(0);
      }
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
  -webkit-animation-duration: 1s;
  animation-duration: 1s;
  -webkit-animation-fill-mode: both;
  animation-fill-mode: both;
}

.player-names.p4 .player:nth-child(1) {
  left: 12.6vw;
  display: block;
}

.player-names.p4 .player:nth-child(2) {
  left: 35.65vw;
  display: block;
}

.player-names.p4 .player:nth-child(3) {
  left: 58.7vw;
  display: block;
}

.player-names.p4 .player:nth-child(4) {
  left: 81.75vw;
  display: block;
}

.player-names.p3 .player:nth-child(1) {
  left: 16.5vw;
  display: block;
}

.player-names.p3 .player:nth-child(2) {
  left: 47.3vw;
  display: block;
}

.player-names.p3 .player:nth-child(3) {
  left: 77.9vw;
  display: block;
}

.player-names.p2 .player:nth-child(1) {
  left: 24.2vw;
  display: block;
}

.player-names.p2 .player:nth-child(2) {
  left: 70.3vw;
  display: block;
}
</style>
