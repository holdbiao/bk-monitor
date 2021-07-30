<template>
  <div class="terminal-instance">
    <pre class="terminal-instance-pre" v-if="animation"><code class="console-code"><div v-for="(item,index) in consoles" :key="index" :class="'status-' + item.status"><span class="code-span" :style="{ animationDelay: `${getDelayTime(index,key)}s` }" v-for="(code,key) in item.text" :key="key">{{code}}</span></div></code></pre>
    <pre class="terminal-instance-pre" v-else ref="instancePre"><code class="console-code"><div ref="consoleCode" v-for="(item,index) in consoles" :key="index" :class="'status-' + item.status">{{item.text}}</div></code></pre>
    <div :class="['bk-icon full-screen-icon', isFull ? 'icon-un-full-screen' : 'icon-full-screen']" @click="toggleFullSreen"></div>
  </div>
</template>
<script>
export default {
  name: 'terminal-instance',
  props: {
    animation: {
      type: Boolean,
      default: true
    },
    delay: {
      type: Number,
      default: 0.005
    },
    consoles: {
      type: Array,
      default() {
        return [
          {
            // eslint-disable-next-line vue/max-len
            text: '[HMR]  - ./node_modules/css-loader/dist/cjs.js!./node_modules/vue-loader/lib/loaders/stylePostLoader.js!./node_modules/sass-loader/lib/loader.js!./node_modules/vue-loader/lib??vue-loader-options!./src/pages/plugin-manager/plugin-instance/terminal-instance/terminal-instance.vue?vue&type=style&index=0&id=66f0afa5&lang=scss&scoped=true&',
            status: 1
          },
          {
            // eslint-disable-next-line vue/max-len
            text: '[HMR]  - ./node_modules/css-loader/dist/cjs.js!./node_modules/vue-loader/lib/loaders/stylePostLoader.js!./node_modules/sass-loader/lib/loader.js!./node_modules/vue-loader/lib??vue-loader-options!./src/pages/plugin-manager/plugin-instance/terminal-instance/terminal-instance.vue?vue&type=style&index=0&id=66f0afa5&lang=scss&scoped=true&',
            status: 2
          },
          {
            // eslint-disable-next-line vue/max-len
            text: '[HMR]  - ./node_modules/css-loader/dist/cjs.js!./node_modules/vue-loader/lib/loaders/stylePostLoader.js!./node_modules/sass-loader/lib/loader.js!./node_modules/vue-loader/lib??vue-loader-options!./src/pages/plugin-manager/plugin-instance/terminal-instance/terminal-instance.vue?vue&type=style&index=0&id=66f0afa5&lang=scss&scoped=true&',
            status: 3
          },
          {
            // eslint-disable-next-line vue/max-len
            text: '[HMR]  - ./node_modules/css-loader/dist/cjs.js!./node_modules/vue-loader/lib/loaders/stylePostLoader.js!./node_modules/sass-loader/lib/loader.js!./node_modules/vue-loader/lib??vue-loader-options!./src/pages/plugin-manager/plugin-instance/terminal-instance/terminal-instance.vue?vue&type=style&index=0&id=66f0afa5&lang=scss&scoped=true&',
            status: 0
          }
        ]
      }
    }
  },
  data() {
    return {
      isFull: false, // 是否全屏
      instancePre: null,
      consoleCode: null
    }
  },
  computed: {
    exitFullscreen() {
      return document.exitFullscreen // W3C
                    || document.mozCancelFullScreen // FireFox
                    || document.webkitExitFullscreen // Chrome等
                    || document.msRequestFullscreen // IE11
    }
  },
  watch: {
    consoles(v) {
      if (v.length) {
        this.$nextTick(() => {
          this.initRefs()
          this.autoScrollToBottom()
        })
      }
    }
  },
  mounted() {
    window.addEventListener('fullscreenchange', this.handleFullScreenChange)
  },
  beforeDestroy() {
    window.removeEventListener('fullscreenchange', this.handleFullScreenChange)
  },
  methods: {
    getDelayTime(index, key) {
      let i = 0
      let count = 0
      while (i < index) {
        count += this.consoles[i].text.length
        i += 1
      }
      const res = (count + key) * this.delay
      return 0.5 + res
    },
    toggleFullSreen() {
      if (!this.isFull) {
        const element = this.$el
        const requestFullscreen = element.requestFullscreen // W3C
                        || element.mozRequestFullScreen // FireFox
                        || element.webkitRequestFullScreen // Chrome等
                        || element.msRequestFullscreen // IE11
        if (requestFullscreen) {
          requestFullscreen.call(element)
        }
      } else {
        if (this.exitFullscreen) {
          this.exitFullscreen.call(document)
        }
      }
    },
    handleFullScreenChange() {
      this.isFull = !this.isFull
    },
    initRefs() {
      this.instancePre = this.instancePre ? this.instancePre : this.$refs.instancePre
      this.consoleCode = this.consoleCode ? this.consoleCode : this.$refs.consoleCode && this.$refs.consoleCode[0]
    },
    autoScrollToBottom() {
      const { instancePre } = this
      const { consoleCode } = this
      if (instancePre && consoleCode) {
        instancePre.scrollTop = consoleCode.scrollHeight
      }
    }
  }
}
</script>
<style lang="scss" scoped>
    $statusColors: #c4c4c4 #b5bd68 #cd0000;

    .terminal-instance {
      display: flex;
      flex: 1;
      height: 100%;
      max-height: 100%;
      max-width: calc(100vw - 477px);
      font-size: 12px;
      &-pre {
        flex: 1;
        background: #313238;
        color: #dcdee5;
        white-space: pre;
        overflow-x: auto;
        border-radius: 0;
        border: 0;
        display: block;
        padding: 9.5px;
        margin: 0;
        line-height: 1.42857143;
        word-break: break-all;
        word-wrap: break-word;

        @for $i from 1 through length($statusColors) {
          .status-#{$i} {
            color: nth($statusColors, $i)
          }
        }
        .console-code {
          padding: 0;
          font-size: inherit;
          color: inherit;
          white-space: pre-wrap;
          background-color: transparent;
          border-radius: 0;

          @keyframes flip-in {
            0% {
              opacity: 0;
            }
            100% {
              opacity: 1;
            }
          }
          .code-span {
            animation: flip-in .05s 0s linear both;
          }
        }
        &::-webkit-scrollbar {
          width: 4px;
          height: 5px;
        }
        &::-webkit-scrollbar-thumb {
          border-radius: 20px;
          background: #aeaeae;
          box-shadow: inset 0 0 6px rgba(204, 204, 204, .3);
        }
      }
      .full-screen-icon {
        position: absolute;
        top: 10px;
        right: 10px;
        margin-right: 5px;
        cursor: pointer;
      }
    }
</style>
