<template>
  <transition
    name="game-info-transition"
    enter-active-class="animated fadeIn"
    leave-active-class="animated fadeOut"
  >
    <div class="game-info" v-if="display_goal">
      <div class="level" :class="level_class"></div>
      <div class="target">
        <div class="title">
          <gradient-text
            height="2vw"
            width="4vw"
            textWidth="60"
            textX="50%"
            textAnchor="middle"
            startColor="#ffe2e2"
            endColor="#d1d0ff"
            text="GOAL"
          ></gradient-text>
        </div>
        <div class="target-score">
          <gradient-text
            height="3vw"
            width="4vw"
            textWidth="40"
            textX="50%"
            textAnchor="middle"
            startColor="#ffd689"
            endColor="#ffbc74"
            :text="this.gameInfo.target_score"
          ></gradient-text>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import GradientText from "/components/GradientText.vue";
import inPlayingMixin from "/js/inPlayingMixin.js";
import _ from "lodash";

export default {
  name: "GameHeader",
  mixins: [inPlayingMixin],
  props: {
    gameInfo: Object,
    config: Object
  },
  components: {
    GradientText
  },
  data() {
    return {};
  },
  computed: {
    display_goal() {
      return this.config.hide_goal != "true" && this.inPlaying;
    },
    level_class() {
      const gameMode = this.gameInfo.game_mode;
      if (_.endsWith(gameMode, "_EASY")) {
        return "easy";
      } else if (_.endsWith(gameMode, "_NORMAL")) {
        return "normal";
      } else if (_.endsWith(gameMode, "_PRO")) {
        return "special";
      }
      return "";
    }
  }
};
</script>

<style scoped>
.game-info {
  position: absolute;
  top: 0.6vw;
  left: 0;
  width: 6vw;
  -webkit-animation-duration: 1s;
  animation-duration: 1s;
  -webkit-animation-fill-mode: both;
  animation-fill-mode: both;
}

.level {
  margin-left: 1vw;
  width: 4vw;
  height: 2.2vw;
  display: block;
  background-size: contain;
  background-repeat: no-repeat;
}

.level.easy {
  background-image: url(/assets/img/ic-level-easy.png);
}

.level.normal {
  background-image: url(/assets/img/ic-level-normal.png);
}

.level.special {
  background-image: url(/assets/img/ic-level-special.png);
}

.title {
  height: 1vw;
  width: 4vw;
  margin-left: 1vw;
  margin-top: -1.2vw;
}
.target-score {
  height: 1vw;
  width: 4vw;
  margin-left: 1vw;
  margin-top: 0.1vw;
}
</style>
