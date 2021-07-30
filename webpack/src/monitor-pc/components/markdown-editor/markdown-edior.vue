<template>
  <div ref="editor"></div>
</template>
<script lang="ts">
import './toastui-editor.css'
import 'codemirror'
import 'codemirror/lib/codemirror.css'
import Editor from './toastui-editor'
import { Vue, Prop, Component, Watch } from 'vue-property-decorator'

@Component({
  name: 'markdown-editor'
})
export default class MarkdownEditor extends Vue {
  editor: any = null
  editorEvents: string[] = ['load', 'change', 'stateChange', 'focus', 'blur']
  valueUpdateMethod: string[] = ['insertText', 'setValue', 'setMarkdown', 'setHtml', 'reset']
  @Prop({
    default: 'tab'
  })
  previewStyle: string
  @Prop({
    default: '500px'
  })
  height: string
  @Prop()
  value: string
  // @Prop({
  //     default: 'markdown'
  // })
  // mode: string
  @Prop()
  options: any
  @Prop()
  html: string
  @Prop({
    default: true
  })
  visible: boolean

  get editorOptions() {
    const options = Object.assign({}, this.options)
    options.initialValue = this.value
    options.initialEditType = 'markdown'
    options.height = this.height
    options.previewStyle = this.previewStyle
    options.hideModeSwitch = true
    return options
  }
  @Watch('previewStyle')
  onPreviewStyleChange(newValue) {
    this.editor.changePreviewStyle(newValue)
  }
  @Watch('value')
  onValueChange(newValue, preValue) {
    if (newValue !== preValue && newValue !== this.editor.getMarkdown()) {
      this.editor.setMarkdown(newValue)
    }
  }
  @Watch('height')
  onHeightChange(newValue) {
    this.editor.height(newValue)
  }
  // @Watch('mode')
  // onModeChange (newValue) {
  //     this.editor.changeMode(newValue)
  // }
  @Watch('html')
  onHtmlChange(newValue) {
    this.editor.setHtml(newValue)
    this.$emit('input', this.editor.getMarkdown())
  }
  @Watch('visible')
  onVisibleChange(newValue) {
    if (newValue) {
      this.editor.show()
    } else {
      this.editor.hide()
    }
  }
  mounted() {
    const eventOption = {}
    this.editorEvents.forEach((event) => {
      eventOption[event] = (...args) => {
        this.$emit(event, ...args)
      }
    })

    const options = Object.assign(this.editorOptions, {
      el: this.$refs.editor,
      events: eventOption
    })

    this.editor = new Editor(options)
    if (this.$listeners.input) {
      this.editor.on('change', () => {
        this.$emit('input', this.editor.getMarkdown())
      })
    }
  }
  destroyed() {
    this.editorEvents.forEach((event) => {
      this.editor.off(event)
    })
    this.editor.remove()
  }
  invoke(methodName, ...args) {
    let result = null
    if (this.editor[methodName]) {
      result = this.editor[methodName](...args)
      if (this.valueUpdateMethod.indexOf(methodName) > -1) {
        this.$emit('input', this.editor.getMarkdown())
      }
    }
    return result
  }
}
</script>
