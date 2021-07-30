<template>
  <div class="custom-desc" :class="{ 'hidden': !value }">
    <div v-for="(desc, index) in descList" :key="index">
      {{index + 1}}. {{desc}}
    </div>
    <span class="custom-desc-btn" @click="$emit('change', false)">{{$t('收起')}}</span>
  </div>
</template>
<script lang="ts">
import { Vue, Prop, Component, Model } from 'vue-property-decorator'
@Component({
  name: 'StrategyCustomDesc'
})
export default class StrategyCustomDesc extends Vue {
  @Prop()
  descList: string[]

  @Model('change', { type: Boolean })
  readonly value!: boolean
}
</script>
<style lang="scss" scoped>
  .custom-desc {
    width: 800px;
    border: 1px solid #a3c5fd;
    background-color: #f0f8ff;
    padding: 10px 35px 10px 10px;
    line-height: 24px;
    margin: -10px 0 20px 36px;
    position: relative;
    transition: height ease-in-out .3s;
    overflow: hidden;
    border-radius: 2px;
    &.hidden {
      height: 0;
      display: none;
    }
    &-btn {
      position: absolute;
      right: 10px;
      top: 10px;
      color: #3a84ff;
      cursor: pointer;
      line-height: 20px;
    }
  }
</style>
