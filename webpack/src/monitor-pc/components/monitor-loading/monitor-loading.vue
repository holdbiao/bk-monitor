<template>
  <transition name="monitor-loading-fade" @after-leave="handleAfterLeave">
    <div
      v-show="visible"
      class="monitor-loading"
      :class="extCls"
      :style="{ backgroundColor: background || '' }">
      <div class="monitor-loading-spinner">
        <span
          v-for="i in 4"
          :key="i"
          class="loading-pointer"
          :class="'pointer-' + i">
        </span>
      </div>
    </div>
  </transition>
</template>

<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
@Component
export default class MonitorLoading extends Vue {
  visible = false
  background = 'rgba(255, 255, 255, 0.9)'
  extCls = ''

  handleAfterLeave(): void {
    this.$emit('after-leave')
  }
}
</script>
<style  lang="scss">
  $colorList: #fd6154 #ffb726 #4cd084 #57a3f1;

  .monitor-loading-fade-enter,
  .monitor-loading-fade-leave-active {
    opacity: 0;
  }
  .monitor-loading {
    position: absolute;
    z-index: 99;
    left: 4px;
    top: 0;
    bottom: 0;
    right: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity .3s;

    @keyframes scale-animate {
      0% {
        transform: scale(1);
      }
      100% {
        transform: scale(.6);
      }
    }
    &-spinner {
      display: flex;
      align-items: center;
      .loading-pointer {
        width: 14px;
        height: 14px;
        transform: scale(.6);
        border-radius: 100%;
        margin-right: 6px;
        animation-name: scale-animate;
        animation-duration: .8s;
        animation-iteration-count: infinite;
        animation-direction: normal;

        @for $i from 1 through length($colorList) {
          &.pointer-#{$i} {
            background-color: nth($colorList, $i);
            animation-delay: ($i * .15s + .1s);
          }
        }
      }
    }
  }
</style>
