<template>
    <i :class="iconClass"></i>
</template>
<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'

type TypeValue = 'level' | 'status' | 'notice'
type AlarmStatus = 'RECOVERED' | 'ABNORMAL' | 'CLOSED'
type StatusMap = {
  [k in AlarmStatus]: string;
}

@Component({
  name: 'icon'
})
export default class Icon extends Vue {
  // icon类别（级别、状态、通知状态）
  @Prop({ default: '' }) private readonly type: TypeValue
  // icon类型
  @Prop({ default: '' }) private readonly status: string | number

  // 事件级别对应icon
  private levelTuple = ['danger', 'mind-fill', 'tips']
  // 告警状态Map
  private statusMap: StatusMap = {
    RECOVERED: 'icon-checked',
    ABNORMAL: 'icon-monitor icon-mc-close',
    CLOSED: 'icon-monitor icon-mc-close'
  }

  get iconClass() {
    if (this.type === 'level') {
      return `icon-monitor icon-${this.levelTuple[this.status as number - 1]}`
    } if (this.type === 'notice') {
      return this.status === 'SUCCESS' ? 'icon-checked' : 'icon-monitor icon-mc-close'
    } if (this.type === 'status') {
      return this.statusMap[this.status]
    }
    return ''
  }
}
</script>
<style lang="scss" scoped>
    @import '../../static/scss/variate.scss';
    $colorList: #ea3636 #ff9c01 #FFD000;
    $statusList: 'danger' 'mind-fill' 'tips';
    @for $i from 1 through 3 {
        .icon-#{nth($statusList, $i)} {
            color: nth($colorList, $i);
            font-size: 14px;
            margin-right: 6px;
            position: relative;
            top: 1px;
        }
    }
    .icon-danger {
        position: relative;
        top: 0px;
    }
    .icon-mc-close {
        font-size: 22px;
        font-weight: bold;
        color: $deadlyColor;
    }
    .icon-checked {
        width: 6px;
        height: 10px;
        border-color: #10C178;
        border-style: solid;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
        margin-right: 6px;
        position: relative;
        top: -1px;
    }
</style>
