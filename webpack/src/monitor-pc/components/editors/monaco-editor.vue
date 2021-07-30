<template>
  <div ref="monacoEditor" :style="{ height: calcSize(renderHeight), width: calcSize(renderWidth), position: 'relative' }">
    <template v-if="fullScreen">
      <span v-if="!isFull" class="icon-monitor icon-fullscreen icon-style" @click="openFullScreen"> </span>
      <span v-else @click="exitFullScreen" class="icon-monitor icon-unfull-screen icon-style" style="right: 20px;"></span>
    </template>
  </div>
</template>

<script lang="ts">
import * as monaco from 'monaco-editor'
import { Prop, Vue, Component, Model, Watch } from 'vue-property-decorator'
import { IMonacoEditorInstance } from '../../types/index'
// @ts-ignore
self.MonacoEnvironment = {
  getWorkerUrl(moduleId, label) {
    if (label === 'json') {
      return process.env.NODE_ENV === 'production'
        ? `${window.static_url}monitor/json.worker.js`
        : './json.worker.js'
    }
    return process.env.NODE_ENV === 'production'
      ? `${window.static_url}monitor/editor.worker.js`
      : './editor.worker.js'
  }
}
@Component
export default class MonacoEditor extends Vue {
  initWidth: number|string = 0
  initHeight = 0
  renderWidth: string | number = '100%'
  renderHeight: string | number = '100%'
  isFull = false
  editor: IMonacoEditorInstance | null = null

  @Model('change', { type: String }) value: string

  @Prop({ type: String, default: 'vs-dark' }) theme: string
  @Prop(String) language: string
  @Prop(Function) amdRequire: undefined
  @Prop(Boolean) fullScreen: boolean
  @Prop({ type: [Number, String], default: '100%' }) width: string
  @Prop({ type: [Number, String], default: 320 }) height: number
  @Prop(Object) options: any

  @Watch('options', { deep: true })
  onOptionsChange(options: any) {
    if (this.editor) {
      this.editor.updateOptions(options)
      this.editor.layout()
    }
  }

  @Watch('value')
  onValueChange(newValue: string) {
    if (this.editor) {
      if (newValue !== this.editor.getValue()) {
        this.editor.setValue(newValue)
      }
    }
  }

  @Watch('language')
  onLanguageChange(newVal: string) {
    this.editor && monaco.editor.setModelLanguage(monaco.editor.getModels()[0], newVal)
  }

  @Watch('theme')
  onThemeChange(newVal: string) {
    this.editor && monaco.editor.setTheme(newVal)
  }

  @Watch('width')
  onWidthChange(newVal: string | number) {
    this.renderWidth = newVal
    this.initWidth = this.width
  }

  @Watch('height')
  onHeightChange(newVal: string | number) {
    this.renderHeight = newVal
    this.initHeight = this.height
  }

  mounted() {
    this.initWidth = this.width
    this.initHeight = this.height
    this.renderWidth = this.width
    this.renderHeight = this.height
    this.initMonaco(monaco)
    window.addEventListener('resize', this.handleFullScreen)
  }

  beforeDestroy() {
    this.editor && this.editor.dispose()
    window.removeEventListener('resize', this.handleFullScreen)
  }

  calcSize(size: string | number): string {
    const _size = size.toString()
    if (_size.match(/^\d*$/)) return `${size}px`
    if (_size.match(/^[0-9]?%$/)) return _size
    return '100%'
  }

  initMonaco(monaco: any): void {
    const options = Object.assign({
      value: this.value,
      theme: this.theme,
      language: this.language,
      fontSize: 16,
      fontFamily: this.$t('微软雅黑'),
      cursorBlinking: 'solid'
    }, this.options)

    this.editor = monaco.editor.create(this.$el, options)
    this.$emit('editorDidMount', this.editor)
    this.editor.onContextMenu(event => this.$emit('contextMenu', event))
    this.editor.onDidBlurEditorWidget(() => this.$emit('blur'))
    this.editor.onDidBlurEditorText(() => this.$emit('blurText'))
    this.editor.onDidChangeConfiguration(event => this.$emit('configuration', event))
    this.editor.onDidChangeCursorPosition((event) => {
      this.$emit('position', event)
    })
    this.editor.onDidChangeCursorSelection((event) => {
      this.$emit('selection', event)
    })
    // this.editor.onDidChangeModel(event => this.$emit('model', event))
    this.editor.onDidChangeModelContent((event) => {
      const value = this.editor.getValue()
      if (this.value !== value) {
        this.$emit('change', value, event)
      }
    })
    this.editor.onDidChangeModelDecorations(event => this.$emit('modelDecorations', event))
    this.editor.onDidChangeModelLanguage(event => this.$emit('modelLanguage', event))
    this.editor.onDidChangeModelOptions(event => this.$emit('modelOptions', event))
    this.editor.onDidDispose(event => this.$emit('afterDispose', event))
    this.editor.onDidFocusEditorWidget(() => this.$emit('focus'))
    this.editor.onDidFocusEditorText(() => this.$emit('focusText'))
    this.editor.onDidLayoutChange(event => this.$emit('layout', event))
    this.editor.onDidScrollChange(event => this.$emit('scroll', event))
    this.editor.onKeyDown(event => this.$emit('keydown', event))
    this.editor.onKeyUp(event => this.$emit('keyup', event))
    this.editor.onMouseDown(event => this.$emit('mouseDown', event))
    this.editor.onMouseLeave(event => this.$emit('mouseLeave', event))
    this.editor.onMouseMove(event => this.$emit('mouseMove', event))
    this.editor.onMouseUp(event => this.$emit('mouseUp', event))
  }

  handleFullScreen(): boolean {
    if (document.fullscreenElement) {
      this.isFull = true
      return true
    } if (this.isFull) {
      this.isFull = false
      this.renderWidth = this.initWidth
      this.renderHeight = this.initHeight
      this.$nextTick().then(() => {
        this.editor.layout()
      })
    }
    return false
  }

  exitFullScreen(): void {
    const exitMethod = document.exitFullscreen // W3C
    if (exitMethod) {
      exitMethod.call(document)
    }
  }

  openFullScreen() {
    const element: any = this.$refs.monacoEditor
    const fullScreenMethod = element.requestFullScreen // W3C
                || element.webkitRequestFullScreen // FireFox
                || element.webkitExitFullscreen // Chrome等
                || element.msRequestFullscreen // IE11
    if (fullScreenMethod) {
      fullScreenMethod.call(element)
      this.renderWidth = window.screen.width
      this.renderHeight = window.screen.height
      this.$nextTick().then(() => {
        this.editor.layout()
      })
    } else {
      this.$bkMessage({
        showClose: true,
        message: this.$t('此浏览器不支持全屏操作，请使用chrome浏览器'),
        theme: 'warning'
      })
    }
  }

  getMonaco(): IMonacoEditorInstance {
    return this.editor
  }

  focus(): void {
    this.editor.focus()
  }
}
</script>
<style lang="scss" scoped>
    .icon-style {
      position: absolute;
      top: 10px;
      right: 15px;
      z-index: 1;
      color: #fff;
      cursor: pointer;
    }
</style>
