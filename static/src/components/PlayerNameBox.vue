<template>
  <div class="player-name-box-wrapper">
    <transition
      name="player-name-box-transition"
      enter-active-class="animated slideInDown"
      leave-active-class="animated slideOutUp"
      :after-leave="requestRemoveFitty"
    >
      <div v-if="isDisplayMyName" class="player-name-box" :class="{ highlight: shouldHighlight }">
        <div class="name" :data-steamid="this.player.steam_id">
          <FittyP :text="display_username" ref="fitty"></FittyP>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import _ from "lodash";
import FittyP from "/components/FittyP.vue";

export default {
  name: "PlayerNameBox",
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
.player-name-box-wrapper {
  width: 16.3vw;
  height: 4.5vw;
  position: absolute;
  top: -1px;
  display: none;
}

.player-name-box {
  width: 100%;
  height: 100%;
  position: absolute;
  background-image: url(/assets/img/nametag.png);
  background-size: contain;
  background-repeat: no-repeat;
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
