<template>
  <div class="auto-complete-input" ref="wrap">
    <!-- 文本类型 -->
    <template v-if="!['file', 'boolean', 'list', 'switch'].includes($attrs.type)">
      <bk-input
        :class="['input-text', { 'password': ['encrypt', 'password'].includes($attrs.type) }]"
        ref="input"
        v-model="params"
        :type="['encrypt', 'password'].includes($attrs.type) ? 'password' : 'text'"
        @input="handleInput">
        <template slot="prepend">
          <slot name="prepend"></slot>
        </template>
      </bk-input>
      <!-- <span ref="tempSpan" class="temp-span">{{params}}</span> -->
      <div v-show="false">
        <ul ref="list" class="auto-complete-input-list">
          <li
            @mousedown="handleMousedown(item, index)"
            class="list-item"
            v-for="(item, index) in tipsData"
            :key="item.name + index"
            v-show="!params || item.name.includes(keyword)">
            {{item.name}}
            <span class="item-desc">{{item.description}}</span>
          </li>
        </ul>
      </div>
    </template>
    <div v-if="$attrs.type === 'file'" class="file-input-wrap">
      <template v-if="config.key === 'yaml'">
        <div v-bkloading="{ isLoading: loading, size: 'mini' }" class="auto-complete-input-file">
          <bk-input
            v-if="allConfig.key === 'yaml'"
            ref="input"
            v-model="params"
            :placeholder="$t('点击上传mib转换后的yaml配置文件')">
            <template slot="prepend">
              <slot name="prepend"></slot>
            </template>
          </bk-input>
          <bk-input
            v-else
            ref="input"
            v-model="params">
            <template slot="prepend">
              <slot name="prepend"></slot>
            </template>
          </bk-input>
          <input class="auto-complete-input-file-input" type="file" ref="upload" accept=".yaml,.yml" @change="fileChange" />
        </div>
      </template>
      <template v-else>
        <div class="prepend">
          <slot name="prepend"></slot>
        </div>
        <div class="file-name">
          <import-file
            class="import-file"
            :file-name="config.default"
            :file-content="config.file_base64"
            @error-message="handleErrorMessage"
            @change="handleFileChange">
          </import-file>
        </div>
      </template>
    </div>
    <div v-else-if="$attrs.type === 'switch'" class="switch-input-wrap">
      <div class="prepend">
        <slot name="prepend"></slot>
      </div>
      <div class="file-name switch-wrap">
        <bk-switcher
          true-value="true"
          false-value="false"
          @change="handleSwitchChange"
          v-model="params">
        </bk-switcher>
      </div>
    </div>
    <!-- list类型 下拉列表 -->
    <template v-if="$attrs.type === 'list'">
      <!-- 当前为security_level选项 -->
      <template v-if="allConfig.key === 'security_level'">
        <div class="auto-complete-input-select">
          <slot name="prepend"></slot>
          <bk-select
            :clearable="false"
            :disabled="false"
            v-model="params"
            @change="handleSelectSecurity"
            ext-cls="select-custom"
            ext-popover-cls="select-popover-custom">
            <bk-option
              v-for="option in allConfig.election"
              :key="option"
              :id="option"
              :name="option">
            </bk-option>
          </bk-select>
        </div>
      </template>
      <!-- 普通选项 -->
      <template v-else>
        <div class="auto-complete-input-select">
          <slot name="prepend"></slot>
          <bk-select
            :disabled="false"
            v-model="params"
            @change="handleSelect"
            ext-cls="select-custom"
            ext-popover-cls="select-popover-custom">
            <bk-option
              v-for="option in allConfig.auth_priv[curAuthPriv].need ? allConfig.auth_priv[curAuthPriv].election : allConfig.election"
              :key="option"
              :id="option"
              :name="option">
            </bk-option>
          </bk-select>
        </div>
      </template>
    </template>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Watch, Emit } from 'vue-property-decorator'
import ImportFile from '../../../plugin-manager/plugin-instance/set-steps/components/import-file.vue'

interface IPopoverInstance {
  hide: (time: number) => void | boolean,
  show: (time: number) => void | boolean,
  destroy: () => void,
  set: (options: any) => void | IPopoverInstance
}
interface ITipsItem {
  name: string,
  description: string
}
@Component({
  name: 'auto-complete-input',
  components: {
    ImportFile
  }
})
export default class StrategySetTarget extends Vue {
  // bkPopover实例对象
  popoverInstance: IPopoverInstance
  // 关键词
  keyword = ''
  // 对外输出参数
  params = ''

  authPriv = ''

  allConfig = {}
  // 补全提示列表offsetX/offsetY
  offsetX = 0
  offsetY = 0
  // 输入旧值
  oldVal = ''
  // 光标在关键字的起始位置
  startIndex = 0
  // 光标的当前位置
  curIndex = 0

  FileNode = null

  // 文件类型loading
  loading = false

  // 当前authPriv
  @Prop({
    type: String,
    default: 'noAuthNoPriv'
  })
  curAuthPriv: string

  // 传入的value
  @Prop({
    type: [String, Boolean, Array, Number, Object],
    default: ''
  })
  value: string

  @Prop({
    type: [Object, String],
    default: ''
  })
  config: {}

  // 补全输入数据
  @Prop({
    default() {
      return []
    }
  })
  tipsData: ITipsItem[]

  @Watch('curAuthPriv')
  handleCurAuthPriv(v) {
    this.authPriv = v
  }

  @Watch('config', {
    immediate: true
  })
  onConfigChange(v) {
    if (v.default !== undefined) {
      this.allConfig = v
      if (v.type === 'file') {
        this.params = v.default.filename
      } else {
        this.params = v.default
      }
    }
  }

  @Emit('file-change')
  handleFileChange(file) {
    return file
  }

  @Emit('error-message')
  handleErrorMessage(msg: string) {
    return msg
  }

  beforeDestroy() {
    this.handleDestroyPopover()
  }

  // 处理输入
  handleInput(val: string, evt: any): void {
    this.handleInputEvt(evt)
    this.getOffset()
    if (!this.params || !this.tipsData.find(item => item.name.includes(this.keyword))) {
      return this.handleDestroyPopover()
    }
    this.handlePopoverShow()
  }

  // 处理输入事件数据
  handleInputEvt(evt): void {
    // 最新值
    const { target } = evt
    const newVal: string = target.value
    this.getIndex(newVal, this.oldVal)
    this.keyword = this.handleKeyword()
    this.oldVal = newVal
    this.emitData(newVal)
  }
  // 处理下拉选项类型
  handleSelect(newVal): void {
    this.emitData(newVal)
  }
  // 处理Security联动
  handleSelectSecurity(newVal): void{
    this.emitData(newVal)
    this.$emit('curAuthPriv', newVal)
  }

  fileChange(e): void{
    if (e.path[0].files[0]) {
      this.loading = true
      // eslint-disable-next-line prefer-destructuring
      const file = e.path[0].files[0]
      const fileName = file.name
      this.params = fileName
      const reader = new FileReader()
      reader.readAsText(file, 'gbk')
      reader.onload = (ev) => {
        // 读取完毕后输出结果
        try {
          const { result } = ev.target
          this.emitData({ filename: fileName, value: result })
          this.loading = false
        } catch (e) {
          this.$bkMessage({
            theme: 'error',
            message: e || this.$t('解析文件失败')
          })
          this.loading = false
        } finally {
          // eslint-disable-next-line
          this.$refs.upload.value = ''
        }
      }
    }
  }
  // 处理开关
  handleSwitch(newVal): void {
    this.emitData(newVal)
  }

  // 处理关键字
  handleKeyword(): string {
    return this.params.slice(this.startIndex, this.curIndex + 1).replace(/({)|(})/g, '')
      .trim()
  }

  // 获取光标的位置
  getIndex(newVal: string, oldVal: string): number {
    const tempStr = newVal.length > oldVal.length ? newVal : oldVal
    let diffIndex = 0
    tempStr.split('').find((item, idx) => {
      diffIndex = idx
      return oldVal[idx] !== newVal[idx]
    })
    this.curIndex = diffIndex
    if ((newVal[diffIndex] === '{') && newVal[diffIndex - 1] === '{') {
      this.startIndex = diffIndex - 1
    }
    // 当出现{{{{
    if (this.curIndex) {
      if (newVal.indexOf('{{{{') > -1) {
        this.curIndex = this.curIndex - 2
        this.startIndex = this.startIndex - 2
      }
    }
    return diffIndex
  }

  // 隐藏
  handleDestroyPopover(): void {
    if (this.popoverInstance) {
      this.popoverInstance.hide(0)
      this.popoverInstance.destroy?.()
      this.popoverInstance = null
    }
  }

  // 提示列表显示方法
  handlePopoverShow(): void {
    // if (!this.$refs.list || this.$refs.wrap) return
    if (!this.popoverInstance) {
      this.popoverInstance = this.$bkPopover(this.$refs.wrap, {
        content: this.$refs.list,
        arrow: false,
        flip: false,
        flipBehavior: 'bottom',
        trigger: 'manul',
        placement: 'top-start',
        theme: 'light auto-complete',
        maxWidth: 520,
        duration: [200, 0],
        offset: `${this.offsetX}, ${this.offsetY}`
      })
    } else {
      // 更新提示的位置
      this.popoverInstance.set({
        offset: `${this.offsetX}, ${this.offsetY}`
      })
    }
    // 显示
    this.popoverInstance.show(100)
  }

  // 点击选中
  handleMousedown(item: ITipsItem): void {
    const paramsArr = this.params.split('')
    paramsArr.splice(this.startIndex, this.curIndex - this.startIndex + 1, item.name)
    this.params = paramsArr.join('')
    this.$emit('input', this.params)
    this.oldVal = this.params
  }

  handleSwitchChange() {
    this.$emit('input', this.params)
  }

  // 计算补全列表的offsetX
  getOffset(): void {
    this.$nextTick(() => {
      const ref: any = this.$refs.input
      const bkInputLeft = ref.$el.getBoundingClientRect().left
      const inputRectLeft = ref.$el.getElementsByTagName('input')[0].getBoundingClientRect().left
      this.offsetX = (inputRectLeft - bkInputLeft)
    })
  }

  // 发送数据
  emitData(val): void{
    this.$emit('input', val)
    this.$emit('autoHandle', val)
  }
}
</script>

<style lang="scss">
.auto-complete-theme {
  padding: 0;
  pointer-events: all;
  border-radius: 0;

  /* stylelint-disable-next-line declaration-no-important */
  box-shadow: none !important;
  font-size: 12px;
  background-color: transparent;
}
</style>

<style lang="scss" scoped>
.auto-complete-input {
  position: relative;
  .temp-span {
    position: absolute;
    top: 0;
    right: -9999px;
    opacity: 0;
  }
  /deep/ .input-text {
    &.password {
      .control-icon {
        display: none;
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
  &-select {
    display: flex;
    flex-direction: row;
    align-items: center;
    .bk-tooltip {
      margin-right: 10px;
    }
    /deep/ .bk-tooltip {
      margin-right: 0;
    }
    /deep/ .prepend-text {
      line-height: 30px;
      padding: 0 20px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      background: #f2f4f8;
      border: 1px solid#c4c6cc;
      border-right: 0;
      position: relative;
      top: 2px
    }
  }
  .file-input-wrap,
  .switch-input-wrap {
    display: flex;
    align-items: center;
    height: 32px;
    /deep/.prepend-text {
      padding: 0 20px;
    }
    .prepend {
      flex-shrink: 0;
      height: 30px;
      line-height: 30px;
      // padding: 0 20px;
      background-color: #f2f4f8;
    }
    .file-name {
      display: flex;
      align-items: center;
      height: 30px;
      flex: 1;
    }
    .switch-wrap {
      padding: 0 10px;
    }
  }
  .file-input-wrap {
    .prepend {
      border: 1px solid #c4c6cc;
      border-right: 0;
      border-top-left-radius: 2px;
      border-bottom-left-radius: 2px;

    }
    .auto-complete-input-file {
      position: relative;
      width: 100%;
      &-input {
        top: 0;
        right: 0;
        opacity: 0;
        position: absolute;
        width: 77%;
        height: 100%;
        cursor: pointer;
      }
    }
    .import-file {
      display: flex;
      align-items: center;
      vertical-align: middle;
    }
  }
  .switch-input-wrap {
    border: 1px solid #c4c6cc;
    .prepend {
      border-right: 1px solid #c4c6cc;
    }
  }
}
</style>
