<template>
  <div class="log-wrapper"
       @mouseover="handleMouseOver"
       @mouseleave="showMask = false"
       @click="handleOpenUpload" :class="{ 'solid': file.show }">
    <div class="mask" v-show="showMask">{{file.base64 ? $t('点击更换') : $t('点击上传')}}</div>
    <div v-if="!file.show" class="log"><span class="text">LOGO</span></div>
    <img class="log-img" v-if="file.show && file.base64.length > 1" :src="file.base64" alt="logo">
    <span class="word-logo" v-if="file.show && file.base64.length === 1">{{file.base64.toUpperCase()}}</span>
    <input ref="uploadImage" accept=".png,.jpg,.jpeg" type="file" style="display: none;" @change="getImageFile">
  </div>
</template>
<script>
export default {
  name: 'logo',
  props: {
    logo: {
      type: String
    }
  },
  data() {
    return {
      file: {
        base64: '',
        show: false
      },
      showMask: false
    }
  },
  watch: {
    logo(val) {
      this.file.base64 = val
      this.file.show = Boolean(val)
    }
  },
  methods: {
    handleMouseOver() {
      this.showMask = true
    },
    handleOpenUpload() {
      this.$refs.uploadImage.click()
    },
    getImageFile(e) {
      const file = e.target.files[0]
      const reader = new FileReader()
      reader.onload = (e) => {
        const { result } = e.target
        this.graphLogo(result)
      }
      reader.readAsDataURL(file)
      e.target.value = ''
    },
    graphLogo(result) {
      const img = new Image()
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      img.onload = () => {
        const originWidth = img.width
        const originHeight = img.height
        let renderWidth = 78
        let renderHeight = 78
        if (originWidth < renderWidth) {
          renderWidth = originWidth
        }
        if (originHeight < renderHeight) {
          renderHeight = originHeight
        }
        canvas.width = renderWidth
        canvas.height = renderHeight
        context.clearRect(0, 0, renderWidth, renderHeight)
        context.drawImage(img, 0, 0, renderWidth, renderWidth)
        this.file.base64 = canvas.toDataURL()
        this.file.show = true
        this.$emit('update:logo', this.file.base64)
      }
      img.src = result
    }
  }
}
</script>
<style lang="scss" scoped>
@import "../../../../static/css/common";

.log-wrapper {
  position: relative;
  border: 1px dashed #dcdee5;
  width: 84px;
  height: 84px;
  border-radius: 2px;
  background-color: #fafbfd;
  z-index: 2;

  @include content-center;
  &.solid {
    border-style: solid;
  }
  .mask {
    position: absolute;
    left: -1px;
    top: -1px;
    width: 84px;
    height: 84px;
    background-color: #63656e;
    opacity: .6;
    color: #fff;
    font-size: 12px;

    @include content-center;
  }
  &:hover {
    cursor: pointer;
    .text {
      display: none;
    }
  }
  .log {
    width: 78px;
    height: 78px;
    text-align: center;
    line-height: 78px;
    border-radius: 50%;
    border: 1px dashed #dcdee5;
    font-size: 12px;
    background-color: #fff;
    color: #979ba5;
  }
  .log-img {
    width: 78px;
    height: 78px;
  }
  .word-logo {
    width: 78px;
    height: 78px;
    font-size: 36px;
    background-color: #63656e;
    color: #fff;
    cursor: pointer;

    @include content-center;
  }
}
</style>
