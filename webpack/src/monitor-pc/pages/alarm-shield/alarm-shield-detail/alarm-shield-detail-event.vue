<template>
  <div class="alarm-shield-detail-event">
    <div class="strategy-detail">
      <div class="strategy-detail-label"> {{ $t('告警内容') }} </div>
      <div class="strategy-detail-content">
        <!-- <div class="column-item">
                    <div class="item-label"> {{ $t('告警级别：') }} </div><div class="item-content">{{levelMap[dimension.level]}}</div>
                </div> -->
        <div class="column-item">
          <div class="item-label"> {{ $t('维度信息：') }} </div><div class="item-content">{{dimension.dimensions}}</div>
        </div>
        <div class="column-item" style="margin-bottom: 18px">
          <div class="item-label"> {{ $t('检测算法：') }} </div><div class="item-content">{{dimension.eventMessage}}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'alarm-shield-detail-event',
  props: {
    dimension: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      levelMap: ['', this.$t('致命'), this.$t('预警'), this.$t('提醒')]
    }
  },
  methods: {
    // 跳转到对应的事件详情
    handleToEvent() {
      this.$router.push({ name: 'event-center-detail', params: { id: this.dimension.id } })
    }
  }
}
</script>

<style lang="scss" scoped>
  .alarm-shield-detail-event {
    font-size: 14px;
    color: #63656e;
    .scope-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 20px;
      .item-label {
        min-width: 90px;
        color: #979ba5;
        text-align: right;
        margin-right: 24px;
      }
      .item-content {
        min-height: 19px;
        display: flex;
        align-items: center;
        .item-icon {
          font-size: 21px;
          color: #979ba5;
          cursor: pointer;
          &:hover {
            color: #3a84ff;
          }
        }
      }
    }
    .adapt-icon {
      /* stylelint-disable-next-line declaration-no-important */
      align-items: center !important;
      .item-content {
        line-height: 23px;
      }
    }
    .strategy-detail {
      display: flex;
      align-items: flex-start;
      margin-bottom: 20px;
      &-label {
        color: #979ba5;
        min-width: 90px;
        text-align: right;
        margin-right: 24px;
        padding-top: 6px;
      }
      &-content {
        display: flex;
        flex-direction: column;
        padding: 18px 21px 0 21px;
        min-width: 836px;
        background: #fafbfd;
        border: 1px solid #dcdee5;
        border-radius: 2px;
        .column-item {
          display: flex;
          align-items: flex-start;
          margin-bottom: 20px;
        }
        .item-label {
          min-width: 70px;
          text-align: right;
          margin-right: 6px;
        }
        .item-content {
          word-wrap: break-word;
          word-break: break-all;
        }
      }
    }
  }
</style>
