<template>
  <div class="empty-target">
    <top-hint v-if="tipShow" class="target-hint">
      <slot>
        {{$t('本次下发覆盖')}}
        {{targetString ? targetString : targetMessage.title + targetMessage.subTitle}}
        <i class="icon-monitor icon-mc-close" @click="tipShow = !tipShow"></i>
      </slot>
    </top-hint>
    <div class="empty-container">
      <div class="register-dialog">
        <div class="loading" v-if="!taskReady.failMsg">
          <svg class="loading-svg" viewBox="0 0 64 64">
            <g>
              <path
                d="M20.7,15c1.6,1.6,1.6,4.1,0,5.7s-4.1,1.6-5.7,0l-2.8-2.8c-1.6-1.6-1.6-4.1,0-5.7s4.1-1.6,5.7,0L20.7,15z"
              />
              <path
                d="M12,28c2.2,0,4,1.8,4,4s-1.8,4-4,4H8c-2.2,0-4-1.8-4-4s1.8-4,4-4H12z"
              />
              <path
                d="M15,43.3c1.6-1.6,4.1-1.6,5.7,0c1.6,1.6,1.6,4.1,0,5.7l-2.8,2.8c-1.6,1.6-4.1,1.6-5.7,0s-1.6-4.1,0-5.7L15,43.3z"
              />
              <path
                d="M28,52c0-2.2,1.8-4,4-4s4,1.8,4,4v4c0,2.2-1.8,4-4,4s-4-1.8-4-4V52z"
              />
              <path
                d="M51.8,46.1c1.6,1.6,1.6,4.1,0,5.7s-4.1,1.6-5.7,0L43.3,49c-1.6-1.6-1.6-4.1,0-5.7s4.1-1.6,5.7,0L51.8,46.1z"
              />
              <path
                d="M56,28c2.2,0,4,1.8,4,4s-1.8,4-4,4h-4c-2.2,0-4-1.8-4-4s1.8-4,4-4H56z"
              />
              <path
                d="M46.1,12.2c1.6-1.6,4.1-1.6,5.7,0s1.6,4.1,0,5.7l0,0L49,20.7c-1.6,1.6-4.1,1.6-5.7,0c-1.6-1.6-1.6-4.1,0-5.7L46.1,12.2z"
              />
              <path
                d="M28,8c0-2.2,1.8-4,4-4s4,1.8,4,4v4c0,2.2-1.8,4-4,4s-4-1.8-4-4V8z"
              />
            </g>
          </svg>
        </div>
        <div>
          <div class="register-msg">{{ taskReady.msg }}</div>
          <div class="wait" v-if="!taskReady.failMsg">{{ $t("请稍等...") }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { transformDataKey } from '../../../../../monitor-common/utils/utils'
import TopHint from './top-hint'
const { i18n } = window
export default {
  name: 'TaskReady',
  components: {
    TopHint
  },
  props: {
    taskReady: {
      type: Object,
      default: {
        msg: i18n.t('采集下发准备中')
      }
    },
    target: {
      type: Object,
      default: () => ({})
    },
    targetString: {
      type: String
    }
  },
  data() {
    return {
      targetMessage: {
        title: '',
        subTitle: ''
      },
      tipShow: true
    }
  },
  watch: {
    target: {
      handler(v) {
        const result = transformDataKey(v)
        const { target, bkTargetType, bkObjType } = result
        const textMap = {
          TOPO: `${this.$t('个')}${this.$t('节点')}`,
          SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
          SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
        }
        if (target?.length) {
          let len = target.length
          if (['TOPO', 'SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(bkTargetType)) {
            const count = target.reduce((pre, item) => {
              const allHost = item.allHost || []
              return Array.from(new Set([...pre, ...allHost]))
            }, []).length
            // 服务模板和集群模板比较特殊，不能直接取target的长度作为数量
            if (['SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(bkTargetType)) {
              const props = bkTargetType.replace('_', '')
              len = target.reduce((pre, item) => (item[props]
                ? Array.from(new Set([...pre, item[props]]))
                : pre
              ), []).length
            }
            this.targetMessage.title = `${len} ${textMap[bkTargetType]}`
            const res = bkObjType === 'SERVICE' ? `${this.$t('个')}${this.$t('实例')}` : `${this.$t('台')}${this.$t('主机')}`
            this.targetMessage.subTitle = `（共 ${count} ${res}）`
          } else {
            this.targetMessage.title = `${len} ${this.$t('台主机')} `
          }
        } else {
          this.targetMessage.title = `0${textMap[bkTargetType]}`
        }
      },
      immediate: true,
      deep: true
    }
  }
}
</script>

<style lang="scss" scoped>
.empty-target {
  height: 500px;
  margin-bottom: 20px;
  .target-hint {
    margin-bottom: 10px;
    /deep/ .hint-text {
      display: flex;
      justify-content: space-between;
      padding-right: 13px;
      .icon-mc-close {
        font-size: 18px;
        cursor: pointer;
        position: relative;
        top: -2px;
      }
    }
  }
  .empty-container {
    height: 452px;
    background: #fff;
    border-radius: 2px;
    border: 1px dashed #dcdee5;
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .register-dialog {
    .loading {
      margin-bottom: 9px;
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
              opacity: #{$i * .125};
            }
          }
        }
      }
    }
    .register-msg {
      text-align: center;
      color: #313238;
      line-height: 1.3;
      margin-bottom: 7px;
      font-size: 24px;
    }
    .wait {
      color: #444;
      font-size: 14px;
      text-align: center;
      margin-bottom: 12px;
    }
  }
}
</style>
