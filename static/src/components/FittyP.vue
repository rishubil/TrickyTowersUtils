<template>
  <p ref="fittyTarget">{{ text }}</p>
</template>

<script>
import fitty from "fitty";
import _ from "lodash";
import { vwToPx } from "/js/utils.js";

export default {
  name: "FittyP",
  props: {
    text: String
  },
  data() {
    return {
      fittyInstance: null
    };
  },
  methods: {
    setFitty() {
      this.fittyInstance = fitty(this.$refs["fittyTarget"], {
        minSize: vwToPx(0.8),
        maxSize: vwToPx(1.6),
        multiLine: false,
        observeWindow: false
      });
    },
    removeFitty() {
      if (this.fittyInstance != null) {
        this.fittyInstance.unsubscribe();
      }
    },
    debouncedUpdateFitty: function() {} // temporary function. It will replaced on created
  },
  created() {
    this.debouncedUpdateFitty = _.debounce(() => {
      this.removeFitty();
      this.setFitty();
    }, 200);
  },
  mounted() {
    document.fonts.ready.then(() => {
      fitty.observeWindow = false;
      this.setFitty();
      window.addEventListener("resize", this.debouncedUpdateFitty, true);
    });
  },
  destroyed() {
    window.removeEventListener("resize", this.debouncedUpdateFitty, true);
  }
};
</script>
