
import _ from "lodash";

const inPlayingMixin = {
  data() {
    return {
      inPlaying: false
    };
  },
  methods: {
    showInPlaying() {
      if (this.shouldInPlaying) {
        this.inPlaying = true;
      }
    },
    hideInPlaying() {
      if (!this.shouldInPlaying) {
        this.inPlaying = false;
      }
    }
  },
  computed: {
    isPlaying() {
      if (this.gameInfo != undefined) {
        if (this.gameInfo.is_playing != undefined) {
          return this.gameInfo.is_playing;
        }
      }
      return false;
    },
    isFinished() {
      if (this.gameInfo != undefined) {
        if (this.gameInfo.is_finished != undefined) {
          return this.gameInfo.is_finished;
        }
      }
      return false;
    },
    shouldInPlaying() {
      return this.isPlaying && !this.isFinished;
    }
  },
  watch: {
    gameInfo(val) {
      if (this.shouldInPlaying) {
        this.showInPlaying();
      } else {
        _.delay(this.hideInPlaying, 2000);
      }
    }
  },
  mounted() {
    if (this.shouldInPlaying) {
      this.showInPlaying();
    } else {
      this.hideInPlaying();
    }
  }
};

export default inPlayingMixin;
