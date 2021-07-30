<template>
  <div class="text-chart">
    <template v-if="series.value">
      <div class="text-chart-value">{{series.value}}</div>
      <div class="text-chart-unit">{{series.unit}}</div>
    </template>
    <div v-else class="text-chart-empty">
      --
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Prop, Component } from 'vue-property-decorator'
import { ITextSeries } from '../options/type-interface'
@Component({
  name: 'TextChart'
})
export default class TextChart extends Vue {
  @Prop({ default() {
    return {
    }
  } }) series: ITextSeries
}
</script>
<style lang="scss" scoped>
.text-chart {
  display: flex;
  flex-wrap: wrap;
  width: 100%;
  height: 30px;
  padding: 0 16px;
  margin: auto;
  &-value {
    color: #3a84ff;
    font-size: 32px;
    font-weight: 500;
    line-height: 30px;
    margin-right: 6px;
  }
  &-unit {
    font-size: 12px;
    color: #979ba5;
    line-height: 20px;
    align-self: flex-end;
  }
  &-empty {
    color: #dcdee5;
    font-size: 50px;
    line-height: 30px;
    margin-left: -16px;
  }
}
</style>
