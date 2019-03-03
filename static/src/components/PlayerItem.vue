<template>
  <div class="player">
    <transition
      name="player-name-box-transition"
      enter-active-class="animated slideInDown"
      leave-active-class="animated slideOutUp"
      :after-leave="requestRemoveFitty"
    >
      <div class="player-info" v-if="isDisplayMyName">
        <div class="player-name-box" :class="{ highlight: shouldHighlight }">
          <div class="name" :data-steamid="this.player.steam_id">
            <fitty-p :text="display_username" ref="fitty"></fitty-p>
          </div>
        </div>
        <div class="player-score">
          <div class="rank" :class="playerRankClass"></div>
          <div class="score">
            <svg xmlns="http://www.w3.org/2000/svg" width="3vw" height="3vw" viewBox="0 0 30 30">
              <defs>
                <linearGradient
                  id="g1"
                  x1="0"
                  x2="0"
                  y1="0"
                  y2="100%"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop stop-color="#ffe2e2" offset="0%"></stop>
                  <stop stop-color="#d1d0ff" offset="100%"></stop>
                </linearGradient>
              </defs>
              <text
                class="svg-score-text"
                x="1"
                y="20"
                fill="url(#g1)"
              >{{ this.player.total_score }}</text>
            </svg>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import _ from "lodash";
import FittyP from "/components/FittyP.vue";

export default {
  name: "PlayerItem",
  props: {
    player: Object,
    isDisplayNames: Boolean,
    config: Object
  },
  components: {
    FittyP
  },
  data() {
    return {};
  },
  computed: {
    playerRankClass() {
      return "rank-" + this.player.rank;
    },
    isDisplayMyName() {
      return this.isDisplayNames && this.player.is_online;
    },
    display_username() {
      const renameConfigKey = "rename_" + this.player.steam_id;
      if (_.has(this.config, renameConfigKey)) {
        return this.config[renameConfigKey];
      }
      return this.player.username;
    },
    shouldHighlight() {
      const highlightConfigKey = "highlight_" + this.player.steam_id;
      if (_.has(this.config, highlightConfigKey)) {
        return this.config[highlightConfigKey] == "true";
      }
      return false;
    }
  },
  methods: {
    requestRemoveFitty() {
      this.$refs.fitty.removeFitty();
    }
  }
};
</script>

<style scoped>
.player {
  width: 16.3vw;
  position: absolute;
  top: -1px;
  display: none;
}

.player-info {
  height: 6.7vw;
}

.player-name-box {
  width: 100%;
  position: absolute;
  background-image: url(/assets/img/nametag.png);
  background-size: contain;
  background-repeat: no-repeat;
  z-index: 3;
}

.player-name-box .name {
  position: relative;
  top: 0;
  height: 3vw;
  bottom: 0;
  overflow: hidden;
  width: 13.6vw;
  margin-top: 1.7vw;
  left: 1.3vw;
  line-height: 1.7vw;
  text-align: center;
  font-weight: 700;
}

.player-name-box.highlight .name {
  animation-iteration-count: infinite;
  -webkit-animation-name: bigPulse;
  animation-name: bigPulse;
  -webkit-animation-duration: 1s;
  animation-duration: 1s;
  -webkit-animation-fill-mode: both;
  animation-fill-mode: both;
}

.player-score {
  position: relative;
  z-index: 5;
  top: 3.5vw;
}

.rank {
  width: 2.8vw;
  height: 3.2vw;
  display: inline-block;
  background-size: contain;
  background-repeat: no-repeat;
}

.rank.rank-1 {
  background-image: url(/assets/img/ic-medal-1.png);
}

.rank.rank-2 {
  background-image: url(/assets/img/ic-medal-2.png);
}

.rank.rank-3 {
  background-image: url(/assets/img/ic-medal-3.png);
}

.rank.rank-4 {
  background-image: url(/assets/img/ic-medal-4.png);
}

.score {
  display: inline-block;
  margin-left: -0.5vw;
}

.svg-score-text {
  font-family: "Noto Sans", sans-serif;
  font-weight: 700;
  font-size: 15px;
  stroke-linejoin: round;
  stroke: #1a0f1f;
  stroke-width: 4px;
  paint-order: stroke;
}

@-webkit-keyframes bigPulse {
  from {
    -webkit-transform: scale3d(1, 1, 1);
    transform: scale3d(1, 1, 1);
  }

  50% {
    -webkit-transform: scale3d(1.2, 1.2, 1.2);
    transform: scale3d(1.2, 1.2, 1.2);
  }

  to {
    -webkit-transform: scale3d(1, 1, 1);
    transform: scale3d(1, 1, 1);
  }
}

@keyframes bigPulse {
  from {
    -webkit-transform: scale3d(1, 1, 1);
    transform: scale3d(1, 1, 1);
  }

  50% {
    -webkit-transform: scale3d(1.2, 1.2, 1.2);
    transform: scale3d(1.2, 1.2, 1.2);
  }

  to {
    -webkit-transform: scale3d(1, 1, 1);
    transform: scale3d(1, 1, 1);
  }
}
</style>
