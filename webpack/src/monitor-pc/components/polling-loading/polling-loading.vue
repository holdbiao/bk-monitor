<template>
  <bk-dialog
    v-model="show"
    :theme="'primary'"
    :close-icon="false"
    header-position="left"
    :show-footer="false">
    <div class="register-dialog">
      <div class="loading" v-if="!status.failMsg">
        <svg class="loading-svg" viewBox="0 0 64 64">
          <g>
            <path d="M20.7,15c1.6,1.6,1.6,4.1,0,5.7s-4.1,1.6-5.7,0l-2.8-2.8c-1.6-1.6-1.6-4.1,0-5.7s4.1-1.6,5.7,0L20.7,15z" />
            <path d="M12,28c2.2,0,4,1.8,4,4s-1.8,4-4,4H8c-2.2,0-4-1.8-4-4s1.8-4,4-4H12z" />
            <path d="M15,43.3c1.6-1.6,4.1-1.6,5.7,0c1.6,1.6,1.6,4.1,0,5.7l-2.8,2.8c-1.6,1.6-4.1,1.6-5.7,0s-1.6-4.1,0-5.7L15,43.3z" />
            <path d="M28,52c0-2.2,1.8-4,4-4s4,1.8,4,4v4c0,2.2-1.8,4-4,4s-4-1.8-4-4V52z" />
            <path d="M51.8,46.1c1.6,1.6,1.6,4.1,0,5.7s-4.1,1.6-5.7,0L43.3,49c-1.6-1.6-1.6-4.1,0-5.7s4.1-1.6,5.7,0L51.8,46.1z" />
            <path d="M56,28c2.2,0,4,1.8,4,4s-1.8,4-4,4h-4c-2.2,0-4-1.8-4-4s1.8-4,4-4H56z" />
            <path d="M46.1,12.2c1.6-1.6,4.1-1.6,5.7,0s1.6,4.1,0,5.7l0,0L49,20.7c-1.6,1.6-4.1,1.6-5.7,0c-1.6-1.6-1.6-4.1,0-5.7L46.1,12.2z" />
            <path d="M28,8c0-2.2,1.8-4,4-4s4,1.8,4,4v4c0,2.2-1.8,4-4,4s-4-1.8-4-4V8z" />
          </g>
        </svg>
      </div>
      <div class="fail" v-else>
        <span class="bk-icon icon-exclamation-circle-shape"></span>
      </div>
      <div>
        <div class="register-msg">{{status.msg}}</div>
        <div class="wait" v-if="!status.failMsg"> {{ $t('请等待...') }} </div>
        <div class="fail-msg" v-else> {{ $t('原因：') }} {{status.failMsg}}</div>
        <div class="close-dialog" v-show="status.failMsg">
          <bk-button :text="true" @click="close"> {{ $t('关闭窗口') }} </bk-button>
        </div>
      </div>
    </div>
  </bk-dialog>
</template>
<script>
export default {
  props: {
    status: {
      type: Object
    },
    show: {
      type: Boolean
    }
  },
  methods: {
    close() {
      this.$emit('update:show', false)
    }
  }
}
</script>
<style lang="scss" scoped>
.register-dialog {
  .loading {
    text-align: center;

    @keyframes loading-ratate {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(-360deg);
      }
    }
    .loading-svg {
      height: 60px;
      width: 60px;
      animation: loading-ratate 1s linear 0s infinite;
      g {
        @for $i from 1 through 8 {
          :nth-child(#{$i}) {
            fill: #3a84ff;
            opacity: #{$i*.125};
          }
        }
      }
    }
  }
  .fail {
    margin-bottom: 16px;
    text-align: center;
  }
  .fail-msg {
    font-size: 12px;
    color: #444;
    text-align: center;
    overflow-wrap: break-word;
  }
  .close-dialog {
    text-align: center;
    margin-top: 12px;
    /deep/ .bk-primary {
      font-size: 12px;
    }
  }
  .icon-exclamation-circle-shape {
    color: #ff9c01;
    font-size: 60px;
  }
  .register-msg {
    text-align: center;
    color: #313238;
    font-size: 20px;
    line-height: 1.3;
    margin-bottom: 10px;
  }
  .wait {
    color: #444;
    font-size: 12px;
    text-align: center;
    margin-bottom: 12px;
  }
}
</style>
