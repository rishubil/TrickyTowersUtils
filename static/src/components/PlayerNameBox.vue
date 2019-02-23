<template>
  <div class="player-name-box">
    <div class="name">
      <p>{{ player.username }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: "PlayerNameBox",
  props: {
    player: Object
  },
  data() {
    return {};
  }
};
</script>

<style scoped>
.player-name-box {
  width: 16.3vw;
  height: 4.5vw;
  position: absolute;
  top: 0;
  display: none;
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
