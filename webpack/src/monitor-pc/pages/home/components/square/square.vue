<template>
  <div class="square" @click.stop="clickHandle">
    <div :class="`square-${status}`">
      <div class="front"></div>
      <div class="bottom"></div>
      <div class="back"></div>
      <div class="top"></div>
      <div class="left"></div>
      <div class="right"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'square',
  props: {
    status: {
      type: String,
      default: 'unset'
    }
  },
  methods: {
    clickHandle() {
      this.$emit('click', this.status)
    }
  }
}
</script>

<style scoped lang="scss">
  @import "../../common/mixins";

  @mixin square($frontColor:#FCFFFC,$topColor:#FCFFFC,$leftColor:#FCFFFC,$backColor:#FCFFFC,$rightColor:#FCFFFC,$bottomColor:#FCFFFC) {
    position: relative;
    width: 150px;
    height: 35px;
    box-sizing: border-box;
    transform-style: preserve-3d;
    transform: rotateX(-20deg) rotateY(45deg) rotateZ(0deg);
    margin: 0px auto;
    div {
      position: absolute;
    }
    .front {
      width: 150px;
      height: 35px;
      transform: translateZ(75px);
      background: $frontColor;
    }
    .bottom {
      width: 150px;
      height: 150px;
      transform: rotateX(270deg) translateZ(-40px);
      background: $bottomColor;
    }
    .back {
      width: 150px;
      height: 35px;
      transform: translateZ(-75px);
      background: $backColor;
    }
    .top {
      width: 150px;
      height: 150px;
      transform: rotateX(90deg) translateZ(75px);
      background: $topColor;
    }
    .left {
      width: 150px;
      height: 35px;
      transform: rotateY(270deg) translateZ(75px);
      background: $leftColor;
    }
    .right {
      width: 150px;
      height: 35px;
      transform: rotateY(90deg) translateZ(75px);
      background: $rightColor;
    }
  }

  .square {
    &-serious {
      @include square(#EB8995, #FFDDDD, #DE6573);
    }
    &-slight {
      @include square(#FFE7A3, #FFF2CC, #FEBF81);
    }
    &-normal {
      @include square(#BCE4B7, #DCFFE2, #85CFB7);
    }
    &-unset {
      @include square(#FCFFFC, #FFFFFF, #F8FFF9);
      .front {
        @include border-dashed-1px(#C4C6CC)
            }
      .left {
        border-right: 0;

        /* stylelint-disable-next-line scss/at-extend-no-missing-placeholder */
        @extend .front;
      }
      .top {
        border-left: 0;
        border-bottom: 0;

        /* stylelint-disable-next-line scss/at-extend-no-missing-placeholder */
        @extend .front;
      }
    }
  }
</style>
