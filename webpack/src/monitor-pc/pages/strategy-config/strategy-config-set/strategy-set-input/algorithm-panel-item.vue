<template>
  <div class="algorithm-panel">
    <span class="panel-mark" :class="typeItem.type + '-color'"></span>
    <div class="panel-title">
      {{typeItem.name}}
    </div>
    <ul class="wrap-list" v-if="alarmData.length">
      <li v-for="(item,index) in alarmData" :key="index" class="wrap-list-item" @mouseenter="item.hover = true" @mouseleave="item.hover = false">
        <div class="item-title">
          <span class="item-title-name">{{item.title}}</span>
          <i class="icon-monitor icon-bianji" v-if="item.hover" @click="handleEditItem(item, index)"></i>
          <i class="icon-monitor icon-mc-close" v-if="item.hover" @click="handleDeleteItem(item, index)"></i>
        </div>
        <algorithms-item :unit="item.algorithmUnit" :algorithm-config="item.config" :type="item.type"></algorithms-item>
      </li>
      <div class="wrap-list-add"
           key="wrap-list-add"
           :class="{ 'check-all': !isCanAdd }"
           @mouseenter="!isCanAdd && handleMouseEnter($event)"
           @mouseleave="!isCanAdd && handleMouseLeave($event)"
           @click="handleAddAlgorithm">
        <i class="icon-monitor icon-jiahao-fill"></i> {{ $t('添加检测算法') }}
      </div>
    </ul>
    <div v-else class="panel-add" @click="handleAddAlgorithm">
      {{ $t('添加检测算法') }}
    </div>
  </div>
</template>
<script>
// import RightPanel from '../../../../components/ip-select/right-panel'
import AlgorithmsItem from '../../strategy-config-detail/algorithms-item'
export default {
  name: 'algorithm-panel-item',
  components: {
    AlgorithmsItem
  },
  props: {
    typeItem: {
      type: Object,
      required: true
    },
    typeId: {
      type: [String, Number],
      required: true
    },
    expand: Boolean,
    alarmData: {
      type: Array,
      required: true
    },
    unit: {
      type: String,
      default: ''
    },
    dataTypeLabel: {
      type: String,
      default: ''
    },
    // 计算公式
    aggMethod: {
      type: String,
      default: ''
    },
    isIcmp: Boolean // 拨测服务的协议类型
  },
  data() {
    return {
      hover: false,
      instance: null
    }
  },
  computed: {
    isCanAdd() {
      // 日志关键字、计算方法为实时、非icmp协议的拨测服务的情况下同一告警等级只允许添加一个检测算法
      return ((this.notIcmp
        || this.aggMethod === 'REAL_TIME') && this.alarmData.length === 0)
        || (this.aggMethod !== 'REAL_TIME'
        && !this.notIcmp && this.alarmData.length < 8)
    },
    notIcmp() {
      return this.typeId === 'uptimecheck' && !this.isIcmp
    }
  },
  watch: {
    isCanAdd(val) {
      if (val && this.instance) {
        this.handleDestroyInstance()
      }
    }
  },
  beforeDestroy() {
    this.handleDestroyInstance()
  },
  methods: {
    handlePanelChange(v, data) {
      this.$emit('panel-change', v, data.level)
    },
    handleAddAlgorithm() {
      this.isCanAdd && this.$emit('add-algorithm', this.typeItem.type, this.typeItem)
    },
    handleEditItem(item, index) {
      this.$emit('edit-algorithm', this.typeItem.type, item, index)
    },
    handleDeleteItem(item, index) {
      this.$emit('delete-algorithm', this.typeItem.type, item, index)
    },
    handleMouseEnter(e) {
      if (!this.instance) {
        this.instance = this.$bkPopover(e.target, {
          arrow: true,
          content: this.$t('检测算法已全部添加，无算法可选')
        })
      }
      this.instance && this.instance.show(100)
    },
    handleMouseLeave() {
      this.instance && this.instance.hide(100)
    },
    handleDestroyInstance() {
      if (this.instance) {
        this.instance.hide(0)
        this.instance.destroy()
        this.instance = null
      }
    }
  }
}
</script>
<style lang="scss" scoped>
  @import "../../../../static/css/common";

  .algorithm-panel {
    border: 1px solid #dcdee5;
    border-radius: 2px;
    background-color: white;
    min-height: 58px;
    margin: 0 40px 8px 0;
    width: calc(100% - 40px);
    position: relative;
    .panel-add {
      color: #979ba5;
      margin: 5px 0 0 16px;
      cursor: pointer;
    }
    &:hover {
      box-shadow: 0 2px 4px 0 rgba(0, 0, 0, .1);
      .panel-add {
        color: #3a84ff;
      }
    }
    .panel-title {
      font-weight: bold;
      margin: 9px 0 0 16px;
      line-height: 16px;
    }
    .panel-mark {
      position: absolute;
      left: -1px;
      top: 11px;
      width: 3px;
      height: 12px;
      &.deadly-color {
        background: $deadlyAlarmColor;
      }
      &.warning-color {
        background: $warningAlarmColor;
      }
      &.remind-color {
        background: $remindAlarmColor;
      }
    }
    .wrap-list {
      padding: 22px 0 12px 20px;
      &-add {
        padding-left: 13px;
        color: #3a84ff;
        position: relative;
        display: flex;
        height: 16px;
        align-items: center;
        margin-top: -10px;
        cursor: pointer;
        width: 150px;
        &.check-all {
          color: #c4c6cc;
        }
        .icon-monitor {
          color: #c4c6cc;
          position: absolute;
          left: -5px;
          top: 2px;
          height: 12px;
        }
      }
      &-item {
        display: flex;
        flex-direction: column;
        position: relative;
        min-height: 48px;
        border-left: 2px solid #c4c6cc;
        padding-left: 12px;
        margin-bottom: 10px;
        .item-title {
          position: absolute;
          top: -13px;
          height: 16px;
          display: flex;
          align-items: center;
          &-name {
            font-weight: bold;
            &:hover {
              color: #313238;
            }
          }
          &::before {
            content: " ";
            position: absolute;
            left: -16px;
            width: 6px;
            height: 6px;
            border-radius: 100%;
            background: #c4c6cc;
          }
          .icon-monitor {
            font-size: 24px;
            color: #ea3636;
            cursor: pointer;
            &.icon-bianji {
              color: #3a84ff;
              margin-left: 2px;
            }
          }
        }
        .item-content {
          margin: 9px 40px 16px 0;
        }
        .item-line {
          height: 0;
          margin-bottom: 16px;
          border-top: 1px dashed #dcdee5;
        }
      }
    }
  }
</style>
