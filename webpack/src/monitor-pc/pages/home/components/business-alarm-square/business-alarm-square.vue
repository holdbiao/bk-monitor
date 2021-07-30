<template>
  <div class="square-svg">
    <div class="square-container">
      <div v-for="(item,index) in squares"
           :class="['item',`item-${index}`,{ 'active': index === selected }]"
           :key="index">
        <square :status="item.status" @click="squareClickHandle(index,item)"></square>
      </div>
    </div>
    <div class="svg-container" v-show="!isAllNormal">
      <svg style="display: none;">
        <symbol id="commonSvg"
                :viewBox="svgMap[curSquare.name].viewBox">
          <path :d="svgMap[curSquare.name].d"
                :stroke="colorMap[curSquare.status]"
                stroke-dasharray="3"
                stroke-width="1.5px" fill="none" />
        </symbol>
      </svg>
      <svg :class="`svg-container-${curSquare.name}`" v-show="selected !== -1">
        <use xlink:href="#commonSvg"></use>
      </svg>
    </div>
  </div>
</template>

<script>
import Square from '../square/square'

export default {
  name: 'business-alarm-square',
  components: { Square },
  props: {
    squares: {
      type: Array,
      default() {
        return []
      }
    },
    status: {
      type: String,
      default: 'serious'
    },
    selectedIndex: {
      type: Number,
      default: 0
    },
    isAllNormal: Boolean
  },
  data() {
    return {
      selected: this.selectedIndex,
      curSquare: this.squares[this.selectedIndex],
      svgMap: {
        uptimecheck: {
          d: 'M0,91.5L0,91.5c15.2,0,27.5-12.3,27.5-27.5V28C27.5,12.8,39.8,0.5,55,0.5h0',
          viewBox: '0 0 55 92'
        },
        process: {
          d: 'M0,185.5L0,185.5c15.2,0,27.5-12.3,27.5-27.5V28C27.5,12.8,39.8,0.5,55,0.5h0',
          viewBox: '0 0 55 186'
        },
        os: {
          d: 'M0,232.5L0,232.5c15.2,0,27.5-12.3,27.5-27.5V28C27.5,12.8,39.8,0.5,55,0.5h0',
          viewBox: '0 0 55 233'
        },
        service: {
          d: 'M0,138.5L0,138.5c15.2,0,27.5-12.3,27.5-27.5V28C27.5,12.8,39.8,0.5,55,0.5h0',
          viewBox: '0 0 55 139'
        }
      },
      colorMap: {
        serious: '#DE6573',
        slight: '#FEBF81',
        unset: '#C4C6CC',
        normal: '#85CFB7'
      }
    }
  },
  methods: {
    squareClickHandle(index, { status, name }) {
      this.selected = index
      this.curSquare = { status, name }
      this.$emit('update:selectedIndex', index)
      if (this.isAllNormal) {
        this.$emit('update:isAllNormal', false)
      }
    }
  }
}
</script>

<style scoped lang="scss">
    @import "../../common/mixins";

    $length: 3 !default;
    $const: 47 !default;

    .square-svg {
      .square-container {
        position: relative;

        @for $i from 0 through $length {
          .item-#{$i} {
            top: -20px + $i*$const;
            z-index: 6 - $i;
          }
        }
        .item {
          position: absolute;
          transition: transform .3s ease-in-out;
          &:hover {
            transform: translateX(25px);
            cursor: pointer;
          }
        }
        .active {
          transform: translateX(25px);
        }
      }
      .svg-container {
        &-uptimecheck {
          @include common-svg();
        }
        &-service {
          @include common-svg(139px);
        }
        &-process {
          @include common-svg(186px);
        }
        &-os {
          @include common-svg(233px);
        }
      }
    }
</style>
