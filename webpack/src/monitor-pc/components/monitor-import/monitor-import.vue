<template>
  <span class="monitor-import" @click="handleClick">
    <slot>{{$t('导入')}}</slot>
    <input ref="fileInput" type="file" :accept="accept" @input="handleInput">
  </span>
</template>
<script lang="ts">
import { Vue, Component, Ref, Prop, Emit } from 'vue-property-decorator'

@Component({ name: 'MonitorImport' })
export default class MonitorExport extends Vue {
  @Prop({ default: false, type: Boolean }) returnFileInfo: boolean
  @Prop({ default: '.json', type: String }) accept: string
  @Prop({ default: false, type: Boolean }) base64: boolean
  @Prop({ default: false, type: Boolean }) disabled: boolean
  @Ref('fileInput') readonly fileInputRef: HTMLElement

  //   @Ref('input') readonly inputRef: HTMLElement

  @Emit('change')
  emitFile(data) {
    return data
  }

  handleClick() {
    !this.disabled && this.fileInputRef.click()
  }

  async handleInput(event: {target: {files: any[], value: ''}}) {
    const [file] = Array.from(event.target.files)
    const fileName = file.name
    let contents = {}
    await new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e: {target: any}) => {
        try {
          if (this.returnFileInfo) {
            contents = {
              name: fileName,
              fileStr: e.target.result,
              size: file.size
            }
          } else {
            contents = e.target.result
          }
          resolve(contents)
          event.target.value = ''
        } catch (e) {
          resolve({})
        }
      }
      if (this.base64) {
        reader.readAsDataURL(file)
      } else {
        reader.readAsText(file, 'UTF-8')
      }
    })
    this.$emit('change', contents)
  }
}
</script>

<style lang="scss" scoped>
.monitor-import {
  position: relative;
  cursor: pointer;
  input[type=file] {
    display: none;
    width: 100%;
    height: 100%;
    position: absolute;
    left: 0;
    top: 0;
    cursor: pointer;
    opacity: 0;
  }
}
</style>
