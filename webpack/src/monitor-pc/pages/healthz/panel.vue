<template>
  <el-card
    :shadow="shadow"
    :body-style="_bodyStyle">
    <div slot="header" class="cf" :style="{ cursor: hiddenAble ? 'pointer' : 'normal' }" @click="trigger">
      <slot name="header"></slot>
      <i v-if="hiddenAble" style="float: right; margin-top: 3px" :class="{ 'el-icon-arrow-down': true, 'rotate-after': isHidden, 'rotate-before': !isHidden }"></i>
    </div>
    <!-- <el-collapse-transition> -->
    <div v-show="!isHidden" style="padding: 20px">
      <slot></slot>
    </div>
    <!-- </el-collapse-transition> -->
  </el-card>
</template>

<script>
import { Card } from 'element-ui'
export default {
  name: 'MoPanel',
  components: {
    ElCard: Card
  },
  props: {
    shadow: {
      type: String,
      default: 'always'
    },
    bodyStyle: {
      type: Object,
      default() {
        return {}
      }
    },
    hiddenAble: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isHidden: false
    }
  },
  computed: {
    _bodyStyle() {
      const body = { display: this.isHidden ? 'none' : 'block' }
      Object.keys(this.bodyStyle).forEach((key) => {
        body[key] = this.bodyStyle[key]
      })
      return body
    }
  },
  methods: {
    trigger() {
      if (this.hiddenAble) {
        this.isHidden = !this.isHidden
      }
    }
  }
}
</script>

<style lang="scss" scoped>

$rotateTime: .3s ease-out;

/deep/ .el-card__header {
  padding: 0;
}
/deep/ .el-card__body {
  padding: 0;
}
.cf {
  padding: 12px 20px;
}
.cf:before,
.cf:after {
  content: "";
  display: table;
}
.cf:after { clear: both; }
.rotate-after {
  transform-origin: center center;
  transform: rotate(180deg);
  transition: transform $rotateTime;
}
.rotate-before {
  transform-origin: center center;
  transform: rotate(0deg);
  transition: transform $rotateTime;
}
</style>
