<template>
  <svg xmlns="http://www.w3.org/2000/svg" :viewBox="viewBox" class="gradient-text">
    <defs>
      <linearGradient id="g1" x1="0" x2="0" y1="0" y2="100%" gradientUnits="userSpaceOnUse">
        <stop :stop-color="startColor" offset="0%"></stop>
        <stop :stop-color="endColor" offset="100%"></stop>
      </linearGradient>
    </defs>
    <text
      class="svg-text"
      :x="textX"
      y="50%"
      dominant-baseline="middle"
      :text-anchor="textAnchor"
      fill="url(#g1)"
    >{{ text }}</text>
  </svg>
</template>

<script>
export default {
  name: "GradientText",
  props: {
    text: String,
    startColor: String,
    endColor: String,
    textWidth: [String, Number],
    textX: {
      type: String,
      default: "1%"
    },
    textAnchor: {
      type: String,
      default: "start",
      validator: value => {
        return ["start", "middle", "end", "inherit"].indexOf(value) !== -1;
      }
    }
  },
  computed: {
    viewBox() {
      return "0 0 " + this.textWidth + " 30";
    }
  }
};
</script>

<style scoped>
.svg-text {
  font-family: "Noto Sans", sans-serif;
  font-weight: 700;
  font-size: 15px;
  stroke-linejoin: round;
  stroke: #1a0f1f;
  stroke-width: 4px;
  paint-order: stroke;
}
</style>
