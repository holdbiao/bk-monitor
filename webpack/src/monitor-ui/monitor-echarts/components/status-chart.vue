<template>
  <ul class="status-chart">
    <template v-if="series.length">
      <template v-for="(item, index) in series">
        <bk-popover
          :content="statusList[item.status]"
          placement="top"
          :key="index">
          <li
            class="status-chart-item"
            :class="`status-${item.status}`">
            {{item.value}}
          </li>
        </bk-popover>
      </template>
    </template>
    <div v-else class="status-chart-empty">
      --
    </div>
  </ul>
</template>
<script lang="ts">
import { Vue, Prop, Component } from 'vue-property-decorator'
@Component({
  name: 'StatusChart'
})
export default class StatusChart extends Vue {
  // 端口列表
  @Prop({ default() {
    return []
  } }) readonly series: {value: string, status: string}[]
  private statusList: any[]
  created() {
    this.statusList = [this.$t('正常'), this.$t('停用'), this.$t('异常')]
  }
}
</script>
<style lang="scss" scoped>
$statusFontColor: #10c178 #c4c6cc #ffb848;
$statusBgColor: #e7f9f2 #f0f1f5 #ffe8c3;

.status-chart {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  width: 100%;
  height: 100%;
  padding: 0;
  &-item {
    display: flex;
    padding: 5px 14px;
    align-items: center;
    justify-content: center;
    line-height: 20px;
    font-size: 12px;
    border-radius: 2px;
    margin: 0 2px 2px 0;
    height: 30px;

    @for $i from 0 through 2 {
      &.status-#{$i} {
        background: nth($statusBgColor, $i + 1);
        color: nth($statusFontColor, $i + 1);
        &:hover {
          background: nth($statusFontColor, $i + 1);
          color: white;
        }
      }
    }
  }
  &-empty {
    color: #dcdee5;
    font-size: 50px;
    line-height: 30px;
  }
}
</style>
