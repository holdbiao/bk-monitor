<template>
  <div class="convergence-options" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
    <i class="icon-monitor icon-mc-close" v-show="isShowCloseIcon && hasCloseIcon" @click="handleClickClose"></i>
    <div class="convergence-options-label">{{ title }}</div>
    <bk-select v-model="checkData" :clearable="false" @change="handleCheckedChange">
      <bk-option
        v-for="(option, index) in selectList"
        :key="index"
        :id="option.id"
        :name="option.name">
      </bk-option>
    </bk-select>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'

@Component({
  name: 'convergence-options'
})
export default class ConvergenceOptions extends Vue {
  @Prop()
  readonly hasCloseIcon: boolean
  @Prop({ default: false })
  readonly isDefault: boolean
  @Prop()
  readonly title: string
  @Prop()
  readonly id: string
  @Prop()
  readonly groupbyList: () => Promise<any[]>


  selectList = []
  isShowCloseIcon = false
  checkData = ''

  created() {
    this.getGroupList()
  }

  async getGroupList() {
    this.selectList = await this.groupbyList()
    if (this.isDefault) {
      this.selectList.unshift({ id: 'all', name: this.$tc('全部') })
      this.checkData = 'all'
    }
  }

  handleMouseEnter() {
    this.isShowCloseIcon = true
  }

  handleMouseLeave() {
    this.isShowCloseIcon = false
  }

  handleClickClose() {
    this.$emit('delete-dimension')
  }

  handleCheckedChange(value) {
    const res = {}
    res[this.id] = value
    this.$emit('checked-change', res)
  }
}
</script>

<style lang="scss" scoped>
.convergence-options {
  width: 320px;
  height: 73px;
  padding: 5px 10px 10px 10px;
  position: relative;
  &-label {
    margin-bottom: 6px;
  }
  &:hover {
    background: #f5f6fa;
    border-radius: 2px;
  }
  .icon-mc-close {
    position: absolute;
    right: 0;
    top: 0;
    font-size: 24px;
    color: #ea3636;
    cursor: pointer;
  }
}
</style>
