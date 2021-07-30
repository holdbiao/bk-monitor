<template>
  <div class="template-input" ref="wrap">
    <div ref="input"
         class="template-input-area"
         contenteditable="true"
         :class="{ 'input-placeholder': !focus }"
         :data-placeholder="defaultPalceholder"
         @blur="handleBlur"
         @click="handleFocus"
         @input="handleInput">
    </div>
    <div v-show="false">
      <ul class="template-input-list" ref="list">
        <template v-for="(item,index) in triggerList">
          <li class="list-item"
              :key="index"
              v-show="!keyword || (item.id && item.id.includes(keyword))"
              @mousedown="handleMousedown(item,index)">
            <span class="item-name">{{item.id}}</span>
            <span class="item-desc">{{item.name}}</span>
          </li>
        </template>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'strategy-template-input',
  props: {
    // 默认显示的值
    defaultValue: {
      type: String,
      default: ''
    },
    // placeholder值
    placeholder: {
      type: String,
      default: ''
    },
    // 触发提示的key值
    triggerKey: {
      type: String,
      default: '{{'
    },
    // 触发提示主动填写后闭合的值
    closeTriggerKey: {
      type: String,
      default: '}}'
    },
    // 触发提示列表
    triggerList: {
      type: Array,
      default() {
        return []
      }
    }
  },
  data() {
    return {
      popoverInstance: null,
      keyword: '',
      focus: false,
      defaultPalceholder: this.$t('请输入告警模板，使用’{{‘触发变量提示'),
      selectedRange: null
    }
  },
  watch: {
    defaultValue(v) {
      if (v !== this.getValue()) {
        this.$refs.input.innerText = v || ''
        this.focus = v.length > 0
      }
    }
  },
  mounted() {
    this.focus = this.defaultValue.length > 0
    this.placeholder && (this.defaultPalceholder = this.placeholder)
    document.execCommand('defaultParagraphSeparator', false, 'div')
    this.$refs.input.innerText = this.defaultValue || ''
  },
  beforeDestroy() {
    this.handleDestroyPopover()
  },
  methods: {
    /**
     * input事件触发
     */
    handleInput() {
      if (this.triggerList.length) {
        const selection = window.getSelection()
        const text = selection.focusNode.wholeText
        this.focus = true
        if (text) {
          const firstText = text.slice(0, selection.focusOffset)
          const matchIndex = firstText.lastIndexOf(this.triggerKey)
          if (matchIndex > -1 && !firstText.slice(matchIndex).match(/}}/gm)) {
            const matchText = firstText.slice(matchIndex)
            this.keyword = matchText.trim().replace(this.triggerKey, '')
              .replace(this.closeTriggerKey, '')
            this.$nextTick().then(() => {
              this.handlePopoverShow()
              if (!this.keyword || this.triggerList.some(item => item.id.includes(this.keyword))) {
                this.popoverInstance && this.popoverInstance.show(100)
              } else {
                this.handleDestroyPopover()
              }
            })
          } else {
            this.handleDestroyPopover()
          }
        } else {
          this.handleDestroyPopover()
        }
      }
      this.$emit('change', this.getValue())
      this.$emit('input', this.getValue())
    },
    /**
     * click事件触发
     */
    handleFocus() {
      const selection = window.getSelection()
      const text = selection.focusNode.wholeText
      this.focus = true
      if (text && selection.focusOffset === text.length && text.slice(text.length - 2) === this.triggerKey) {
        this.$nextTick().then(() => {
          this.handlePopoverShow()
          this.popoverInstance && this.popoverInstance.show(100)
        })
      }
      this.$emit('focus', this.getValue())
    },
    /**
     * input失去焦点触发
     */
    handleBlur(e) {
      e.preventDefault()
      this.focus = this.getValue().length > 0
      this.$emit('blur', e)
    },
    /**
     * 提示列表项选中事件触发
     */
    handleMousedown(item) {
      const selection = window.getSelection()
      const text = selection.focusNode.wholeText
      const nextText = text.slice(selection.focusOffset)
      const nextCloseIndex = nextText.indexOf(this.closeTriggerKey)
      const nextOpenIndex = nextText.indexOf(this.triggerKey)
      if (nextCloseIndex >= -1 && (nextOpenIndex === -1 || nextOpenIndex > nextCloseIndex)) {
        const firstText = text.slice(0, selection.focusOffset)
        const startOpenIndex = firstText.lastIndexOf(this.triggerKey)
        document.execCommand(
          'insertText',
          false,
          `{{${item.id}}}`.replace(firstText.slice(startOpenIndex), '')
            .replace(nextText.slice(0, nextCloseIndex + 2), '')
        )
      } else {
        document.execCommand('insertText', false, item.id + this.closeTriggerKey)
      }
      this.$emit('item-click', item, this.getInputInstance())
    },
    /**
     * 提示列表显示方法
     */
    handlePopoverShow() {
      const range = window.getSelection().getRangeAt(0)
      const rect = range.getBoundingClientRect()
      const inputRect = this.$refs.input.getBoundingClientRect()
      const offsetX = rect.x - inputRect.x + 8
      const offsetY = -12 - (this.$refs.wrap.clientHeight - rect.y + inputRect.y) + 18
      if (!this.popoverInstance) {
        this.popoverInstance = this.$bkPopover(this.$refs.wrap, {
          content: this.$refs.list,
          arrow: false,
          flip: false,
          flipBehavior: 'bottom',
          trigger: 'manul',
          placement: 'bottom-start',
          theme: 'light set-input-list',
          maxWidth: 520,
          duration: [200, 0],
          offset: `${offsetX}, ${offsetY}`,
          onHidden: this.handleFocusToEnd
        })
      } else {
        this.popoverInstance.set({
          offset: `${offsetX}, ${offsetY}`
        })
      }
    },
    /**
     * 提示列表项弹窗隐藏及销毁方法
     */
    handleDestroyPopover() {
      if (this.popoverInstance) {
        this.popoverInstance.hide(0)
        this.popoverInstance.destroy && this.popoverInstance.destroy()
        this.popoverInstance = null
      }
    },
    /**
     * 设置光标在行尾
     */
    handleFocusToEnd() {
      const timer = setTimeout(() => {
        if (this.$refs.input) {
          this.$refs.input.focus() // 解决ff不获取焦点无法定位问题
          const selection = window.getSelection()// 创建range
          if (selection.focusOffset === 0) {
            selection.selectAllChildren(this.$refs.input)// range 选择obj下所有子内容
            selection.collapseToEnd()// 光标移至最后
          }
        }
        window.clearTimeout(timer)
      }, 20)
    },
    /**
     * 获取告警模板值
     */
    getValue() {
      return this.$refs.input.innerText || ''
    },
    /**
     * 获取input dom实例
     */
    getInputInstance() {
      return this.$refs.input
    }
  }
}
</script>
<style lang="scss" scoped>
    .template-input {
      display: flex;
      max-width: 100%;
      min-height: 60px;
      overflow: auto;
      border: 1px solid #dcdee5;
      border-radius: 2px;
      background: #fff;
      position: relative;
      &-area {
        padding: 6px 12px;
        width: calc(100% - 5px);
        height: 100%;
        font-size: 12px;
        line-height: 16px;
        &.input-placeholder {
          &:before {
            content: attr(data-placeholder);
            color: #c4c6cc;
          }
        }
      }
      &-list {
        border: 1px solid #dcdee5;
        border-radius: 2px;
        display: flex;
        flex-direction: column;
        width: 420px;
        overflow: auto;
        max-height: 300px;
        box-shadow: 0px 3px 6px 0px rgba(0,0,0,.15);
        padding: 6px 0;
        .list-item {
          flex: 0 0 32px;
          height: 32px;
          display: flex;
          align-items: center;
          padding: 0 12px 0 15px;
          color: #63656e;
          font-size: 12px;
          .item-desc {
            color: #c4c6cc;
            margin-left: auto;
          }
          &:hover {
            color: #3a84ff;
            background-color: #e1ecff;
            cursor: pointer;
            .item-desc {
              color: #a3c5fd;
            }
          }
        }
      }
    }
</style>
