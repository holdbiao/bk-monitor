<template>
  <div class="right-panel" :class="{ 'need-border': needBorder }">
    <div @click="handleTitleClick" class="right-panel-title" :class="{ 'is-collapse': isEndCollapse }" :style="{ 'backgroundColor': titleBgColor }">
      <slot name="panel">
        <slot name="pre-panel"></slot>
        <i class="bk-icon title-icon" :style="{ 'color': collapseColor }" :class="[collapse ? 'icon-down-shape' : 'icon-right-shape']"></i>
        <div class="title-desc">
          <slot name="title"> {{ $t('已选择') }} <span class="title-desc-num">{{title.num}}</span>
            {{title.type ? `${$t('主机单位')}${title.type}` : `${$t('主机单位')}${$t('主机')}`}}
          </slot>
        </div>
      </slot>
    </div>
    <transition :css="false"
                @before-enter="beforeEnter" @enter="enter" @after-enter="afterEnter"
                @before-leave="beforeLeave" @leave="leave" @after-leave="afterLeave" @leave-cancelled="afterLeave">
      <div class="right-panel-content" v-show="collapse">
        <slot>

        </slot>
      </div>
    </transition>
  </div>
</template>
<script>
export default {
  name: 'right-panel',
  model: {
    prop: 'collapse',
    event: 'change'
  },
  props: {
    collapse: Boolean,
    title: {
      type: Object,
      default() {
        return {
          num: 0,
          type: ''
        }
      }
    },
    collapseColor: {
      type: String,
      default: '#63656E'
    },
    titleBgColor: {
      type: String,
      default: '#F5F6FA'
    },
    type: String,
    needBorder: Boolean
  },
  data() {
    return {
      isEndCollapse: this.collapse
    }
  },
  methods: {
    beforeEnter(el) {
      el.classList.add('collapse-transition')
      el.style.height = '0'
    },
    enter(el) {
      el.dataset.oldOverflow = el.style.overflow
      if (el.scrollHeight !== 0) {
        el.style.height = `${el.scrollHeight}px`
      } else {
        el.style.height = ''
      }
      this.$nextTick().then(() => {
        this.isEndCollapse = this.collapse
      })
      el.style.overflow = 'hidden'
      setTimeout(() => {
        el.style.height = ''
        el.style.overflow = el.dataset.oldOverflow
      }, 300)
    },
    afterEnter(el) {
      el.classList.remove('collapse-transition')
    },
    beforeLeave(el) {
      el.dataset.oldOverflow = el.style.overflow
      el.style.height = `${el.scrollHeight}px`
      el.style.overflow = 'hidden'
    },
    leave(el) {
      if (el.scrollHeight !== 0) {
        el.classList.add('collapse-transition')
        el.style.height = 0
      }
      setTimeout(() => {
        this.isEndCollapse = this.collapse
      }, 300)
    },
    afterLeave(el) {
      el.classList.remove('collapse-transition')
      setTimeout(() => {
        el.style.height = ''
        el.style.overflow = el.dataset.oldOverflow
      }, 300)
    },
    handleTitleClick() {
      this.$emit('update:collapse', !this.collapse)
      this.$emit('change', !this.collapse, this.type)
    }
  }
}
</script>
<style lang="scss" scoped>
    .right-panel {
        &.need-border {
            border: 1px solid #DCDEE5;
            border-radius: 2px;
        }
        &-title {
            display: flex;
            height: 40px;
            color: #63656E;
            font-weight: bold;
            align-items: center;
            padding: 0 16px;
            cursor: pointer;
            &.is-collapse {
                border-bottom: 1px solid #DCDEE5;
                height: 41px;
            }
            .title-icon {
                font-size: 14px;
                margin-right: 5px;
                &:hover {
                    cursor: pointer;
                }
            }
            .title-desc {
                color: #979BA5;
                &-num {
                    color: #3A84FF;
                    margin: 0 3px;
                }
            }
            &:hover {
                background: #F0F1F5 !important;
            }
        }
        &-content {
            /deep/ .bk-table{
                border: 0;
                .bk-table-header {
                    th {
                        background: #FFFFFF;
                    }
                }
                &::after {
                    width: 0;
                }
            }
        }
        .collapse-transition {
            transition: 0.3s height ease-in-out;
        }
    }
</style>
