<template>
  <span :class="['switcher-wrapper', { 'switch-acitve': value }]">
    <input type="checkbox" :checked="value" @change="handleChange">
  </span>
</template>

<script lang='ts'>
import { Vue, Component, Prop } from 'vue-property-decorator'

@Component({
  name: 'switcher'
})
export default class Switcher extends Vue {
  // checkbox的状态
  @Prop({ default: false, required: true }) readonly value: boolean

  handleChange(evt) {
    this.$emit('input', evt.target.checked)
    this.$emit('change', evt)
  }
}
</script>

<style lang="scss" scoped>
  @import "../../static/css/common.scss";

  .switcher-wrapper {
    position: relative;
    display: inline-block;
    width: 24px;
    height: 10px;
    &::before {
      position: absolute;
      content: "";
      top: 50%;
      left: 0;
      width: 100%;
      height: 4px;
      transform: translate3D(0, -50%, 0);
      border-radius: 2px;
      background-color: $slightFontColor;
      will-change: background-color;
      transition: all .4s ease;
    }
    &::after {
      position: absolute;
      content: "";
      top: 0;
      left: 3px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background-color: $defaultFontColor;
      will-change: background-color, left;
      transition: all .4s ease;
    }
    input[type=checkbox] {
      position: absolute;
      opacity: 0;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
      cursor: pointer;
    }
  }
  .switch-acitve {
    &::before {
      background-color: #a3c5fd;
    }
    &::after {
      left: 11px;
      background-color: $primaryFontColor;
    }
  }
</style>
